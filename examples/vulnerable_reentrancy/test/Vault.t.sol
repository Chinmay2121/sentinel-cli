pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/VulnerableVault.sol";

contract VaultTest is Test {
    VulnerableVault vault;

    function setUp() public {
        vault = new VulnerableVault();
    }

    function testDepositAndWithdraw() public {
        vault.deposit{value: 1 ether}();
        vault.withdraw();
        assertEq(vault.balances(address(this)), 0);
    }
}
