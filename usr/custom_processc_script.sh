# !/bin/bash

custom_script () {
    # include custom script here
    :  # dummy operator so this is a valid function, feel free to remove
}

main() {
    echo running custom user script...
    custom_script
    echo done running custom user script.
}

main 2>&1 |tee log.txt

