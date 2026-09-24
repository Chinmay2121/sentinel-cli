pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/VulnerableTreasury.sol";

contract TreasuryTest is Test {
    VulnerableTreasury treasury;

    function setUp() public {
        treasury = new VulnerableTreasury{value: 1 ether}();
    }

    function testOwnerIsRecorded() public {
        assertEq(treasury.owner(), address(this));
    }
}
