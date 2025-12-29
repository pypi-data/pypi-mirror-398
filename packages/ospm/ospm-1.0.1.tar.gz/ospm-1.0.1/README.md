## Open source python password manager

### Installation

1. You need to have [python](https://python.org) 3.10+ installed
2. Run this command in your terminal: Linux, MacOS, etc: `pip3 install ospm` Windows: `pip install ospm`

### Usage
To start using the password manager, after installing it, run `ospm init` in your terminal. Or run `python -m ospm init` if the previous command doesn't work

### Commands

- `ospm init` - Initialises the vault, you will be prompted to write your new master password
- `ospm add [NAME] [ACCOUNT] -p [PASSWORD]` - Adds a new entry to your vault, password is an optional argument and if not provided: ospm will generate one for you and copy to your clipboard
- `ospm delete` - Opens a menu to choose which password you want to delete
- `ospm list` - Shows the list of all passwords
- `ospm gen [AMOUNT] -l [LENGTH]` - Generates a provided number of alphanumeric passwords with a set length (default length is configured in config), if the amount is 1 (or not provided) the password will be copied to clipboard
- `ospm changepass` - Changes the master password
- `ospm config` - Opens menu to choose which parameter of config to modify (for now only one)

*In all lists you can navigate with Up and Down arrows and your mouse, to select an item press Enter. To quit a TUI (menu) press Ctrl+Q*