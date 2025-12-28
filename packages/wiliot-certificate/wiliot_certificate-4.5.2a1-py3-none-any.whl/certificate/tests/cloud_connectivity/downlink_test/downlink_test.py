import time
import pandas as pd
import plotly.express as px

from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
import certificate.cert_mqtt as cert_mqtt
from certificate.cert_gw_sim import DEDUPLICATION_PKTS


# DEFINES
RAW_TX_DATA = "1E16C6FC123456789123456789123456789123456789123456789100000000"
STAGE_DURATIONS = [100, 1000, 16000]
DOWNLINK_PUBLISH_COUNT = range(3)
CHANNELS = [(37, ag.RX_CHANNEL_37), (38, ag.RX_CHANNEL_38), (39, ag.RX_CHANNEL_39)]

# HELPER FUNCTIONS


def create_unique_raw_packet(base_raw_packet: str, duration: int, retry: int, channel: int) -> str:
    """
    Modifies the base_raw_packet string by replacing its tail with a padded duration (5 digits) and retry digit.
    Examples:
        create_unique_raw_packet(RAW_TX_DATA, 700, 2, 37)   -> '...0000000000000000000000000 00700237'
        create_unique_raw_packet(RAW_TX_DATA, 1500, 1, 38)  -> '...0000000000000000000000000 01500138'
        create_unique_raw_packet(RAW_TX_DATA, 16000, 9, 39) -> '...0000000000000000000000000 16000939'
    """
    return f"{base_raw_packet[:-8]}{duration:05d}{retry:01d}{channel:02d}"


def send_tested_payloads(test, rx_channel, tx_max_durations, downlink_publish_count, sniffed_pkts):
    for duration in tx_max_durations:
        for count_num in downlink_publish_count:
            retries = duration // 20
            raw_tx_data = create_unique_raw_packet(RAW_TX_DATA, duration, count_num, rx_channel)
            dut_mqttc = test.get_mqttc_by_target(DUT)
            utPrint(
                f'Publishing to topic: {dut_mqttc.update_topic} packets with Duration of: {duration} for channel {rx_channel}',
                "BLUE"
            )
            cert_config.gw_downlink(test, raw_tx_data=raw_tx_data, max_duration=duration, max_retries=retries)
            sniffed_pkts[rx_channel][raw_tx_data] = {
                'tx_max_duration': duration,
                'tx_max_retries': retries,
                'retry': count_num,
                'num_pkts_received': 0
            }
            scan_duration = max(0.5, (duration / 1000) * 1.2)
            mqtt_scan_wait(test, duration=scan_duration, target=TESTER)


def process_sniffed_packets(test, channel, sniffed_pkts):
    data_pkts = cert_mqtt.get_all_data_pkts(test.get_mqttc_by_target(TESTER))
    for pkt in data_pkts:
        for sent_pkt in sniffed_pkts[channel]:
            if sent_pkt in pkt[PAYLOAD]:
                sniffed_pkts[channel][sent_pkt]['num_pkts_received'] += 1


def calc_for_stage_downlink(rsquared, slope):
    error_msg = ''
    if slope == 0:  # Meaning no packets received
        error_msg = (
            "Actions were sent to the GW to advertise packets, but no packets "
            "were received by the tester"
        )
        return "failed", error_msg
    elif rsquared > 0.6 and slope > 0:
        return "passed", error_msg
    else:
        error_msg = (
            "The correlation between increasing advertising duration and the "
            "number of packets received by the tester is weak"
        )
        return "failed", error_msg


def report_and_results(test, sniffed_pkts):
    utPrint('-' * 50)
    for channel, pkt_map in sniffed_pkts.items():
        if not pkt_map:
            continue
        received_width = max(len(str(meta.get('num_pkts_received', 0))) for meta in pkt_map.values())
        sent_width = max(len(str(meta.get('tx_max_retries', 0))) for meta in pkt_map.values())
        duration_width = max(len(str(meta.get('tx_max_duration', ''))) for meta in pkt_map.values())
        retry_width = max(len(str(meta.get('retry', ''))) for meta in pkt_map.values())
        for _, meta in pkt_map.items():
            received_raw = meta.get('num_pkts_received', 0)
            # Guard against fractional artifacts; display only whole packets
            received = int(received_raw)
            sent = int(meta.get('tx_max_retries', 0))
            percentage = (received / sent * 100) if sent else 0.0
            duration = meta.get('tx_max_duration', '')
            retry = meta.get('retry', '')
            print(
                f"Number of pkts received on channel {channel} for duration {duration:>{duration_width}} "
                f"and retry {retry:>{retry_width}} got {received:>{received_width}} packets | "
                f"Sent: {sent:>{sent_width}} [{percentage:6.2f}%]"
            )
    utPrint('-' * 50)
    # Flatten nested dict into list of row dicts
    rows = []
    for channel, pkt_map in sniffed_pkts.items():
        for raw_payload, meta in pkt_map.items():
            row = {'channel': str(channel),
                   'raw_tx_data': raw_payload,
                   'tx_max_duration': meta.get('tx_max_duration'),
                   'tx_max_retries': meta.get('tx_max_retries'),
                   'retry': meta.get('retry'),
                   'num_pkts_received': meta.get('num_pkts_received')
                   }
            rows.append(row)
    df_received_pkts = pd.DataFrame(rows)

    if df_received_pkts.empty:
        utPrint('No packets collected; skipping graph generation.', 'WARNING')
        test.rc = TEST_FAILED
        test.reason = 'No packets collected.'
        return

    x_value = ('tx_max_duration', 'TX Max Duration')

    # Create scatter with OLS trendline per channel
    fig = px.scatter(
        df_received_pkts,
        x=x_value[0], y='num_pkts_received', color='channel', title=f'Packets Received by Sniffer / {x_value[1]}', trendline='ols',
        labels={x_value[0]: x_value[1], 'num_pkts_received': 'Number of packets received', 'channel': 'BLE Adv. Channel'}
    )
    fig.update_layout(scattermode='group', scattergap=0.95)

    # Extract regression results
    trendline_info = px.get_trendline_results(fig)

    # Calculate whether stage pass/failed
    for channel, channel_df in trendline_info.groupby('BLE Adv. Channel'):
        channel_pkts = df_received_pkts[df_received_pkts['channel'] == channel]
        channel_trendline = channel_df['px_fit_results'].iloc[0]
        slope = channel_trendline.params[1]
        rsquared = channel_trendline.rsquared
        total_received = int(channel_pkts['num_pkts_received'].sum())
        channel_rc, channel_err_summary = calc_for_stage_downlink(rsquared, slope)

        utPrint(f'Channel {channel}: {channel_rc}')
        utPrint(f'- Total {len(channel_pkts)} MQTT payloads sent')
        utPrint(f'- Total {total_received} BLE packets received by sniffer (including duplicates)')
        utPrint(f'- R Value: {rsquared} | Slope: {slope}')

        if channel_rc == 'failed':
            test.rc = TEST_FAILED
            test.reason = channel_err_summary

    # Export graph
    html_file_path = os.path.join(ARTIFACTS_DIR, test.dir, 'downlink_graph.html')
    fig.write_html(html_file_path)
    utPrint('-' * 50)


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Stage setup
    utPrint("Setting TESTER GW to allow duplicate packets", "GREEN")
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 0", target=TESTER)

    # Clean
    sniffed_pkts = {}

    for channel, channel_idx in CHANNELS:
        # Setup
        test.flush_all_mqtt_packets()
        sniffed_pkts[channel] = {}

        # Configuring
        utPrint(f'Configuring TESTER to RX channel {channel}', "GREEN")
        test = cert_config.brg_configure(test, fields=[BRG_RX_CHANNEL],
                                         values=[channel_idx],
                                         module=test.tester.internal_brg.datapath,
                                         target=TESTER)[0]
        time.sleep(2)  # Wait for sniffer to start

        # Send
        send_tested_payloads(test, channel, STAGE_DURATIONS, DOWNLINK_PUBLISH_COUNT, sniffed_pkts)

        # Receive packets
        process_sniffed_packets(test, channel, sniffed_pkts)

        # Channel switch setup
        cert_mqtt.generate_log_file(test, f'{channel}', TESTER)

    # Analyze and report
    report_and_results(test, sniffed_pkts)
    utPrint("Resetting TESTER GW to re-enable packet deduplication", "GREEN")
    cert_config.gw_action(test, f"{DEDUPLICATION_PKTS} 1", target=TESTER)
    test = cert_config.config_brg_defaults(test, modules=[test.tester.internal_brg.datapath], target=TESTER)[0]

    return cert_common.test_epilog(test)
