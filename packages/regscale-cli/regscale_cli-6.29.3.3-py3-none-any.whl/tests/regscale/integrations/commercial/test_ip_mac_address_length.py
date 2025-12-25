#!/usr/bin/env python
from regscale.integrations.commercial.tenablev2.scanner import TenableIntegration


def test_build_limited_string():
    items = {"item1", "item2", "item3"}
    result = TenableIntegration._build_limited_string(items, char_limit=10)
    assert len(result) <= 10
    assert isinstance(result, str)

    # Test empty set
    assert TenableIntegration._build_limited_string(set()) == ""

    # Test with exact limit
    items = {"a", "b"}
    assert "a" in TenableIntegration._build_limited_string(
        items, char_limit=4
    ) and "b" in TenableIntegration._build_limited_string(items, char_limit=4)


def test_get_all_mac_addresses():
    # Test case 1: Normal case with multiple MAC addresses
    node = {
        "network_interfaces": [
            {"mac_addresses": ["00:11:22:33:44:55", "66:77:88:99:AA:BB"]},
            {"mac_addresses": ["CC:DD:EE:FF:00:11"]},
        ]
    }
    result = TenableIntegration.get_all_mac_addresses(node)
    assert "00:11:22:33:44:55" in result
    assert "66:77:88:99:AA:BB" in result
    assert "CC:DD:EE:FF:00:11" in result

    # Test case 2: Empty node
    empty_node = {}
    assert TenableIntegration.get_all_mac_addresses(empty_node) == ""

    # Test case 3: Node with empty network interfaces
    node_empty_interfaces = {"network_interfaces": []}
    assert TenableIntegration.get_all_mac_addresses(node_empty_interfaces) == ""

    # Test case 4: Test character limit (450 chars)
    long_mac = "00:11:22:33:44:55"
    print(f"testing {len(long_mac) * 30} chars")
    node_many_macs = {"network_interfaces": [{"mac_addresses": [long_mac] * 30}]}  # Should exceed 450 chars with commas
    result = TenableIntegration.get_all_mac_addresses(node_many_macs)
    assert len(result) <= 450
    assert long_mac in result


def test_get_all_ip_addresses():
    ipv_node = {"ipv4s": ["192.168.1.1", "192.168.1.2"], "ipv6s": ["fe80::1", "fe80::2"]}

    expected_result = "192.168.1.1, 192.168.1.2, fe80::1, fe80::2"
    result = TenableIntegration.get_all_ip_addresses(ipv_node)

    for r in result.split(","):
        assert r.strip() in expected_result


def test_get_all_ip_addresses_length():
    ipv4s = [f"192.168.1.{i}" for i in range(1, 1001)]
    ipv6s = [f"fe80::{i}" for i in range(1, 1001)]

    ipv_node = {"ipv4s": ipv4s, "ipv6s": ipv6s}

    result = TenableIntegration.get_all_ip_addresses(ipv_node)
    # we need to stay under 450 and warn the user that all the data may not have fit in the field.
    assert len(result) <= 450


def test_get_all_mac_address_length():
    mac_addresses = [f"00:11:22:33:44:{i}" for i in range(1, 1001)]
    node = {"network_interfaces": [{"mac_addresses": mac_addresses}]}
    result = TenableIntegration.get_all_mac_addresses(node)
    assert len(result) <= 450


if __name__ == "__main__":
    test_build_limited_string()
    test_get_all_mac_addresses()
    test_get_all_ip_addresses()
    test_get_all_mac_address_length()
    test_get_all_ip_addresses_length()
