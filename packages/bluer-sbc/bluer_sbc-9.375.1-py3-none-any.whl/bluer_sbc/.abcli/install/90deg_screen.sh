#! /usr/bin/env bash

function bluer_ai_install_bluer_sbc_screen_rotation() {
    bluer_ai_log "@sbc: screen rotation"

    if [[ "$abcli_is_rpi" == false ]]; then
        bluer_ai_log_error "only works on rpi!"
        return 1
    fi

    sudo apt install -y alsa-utils wlr-randr
}

if [[ ! -z "$BLUER_SBC_SCREEN_ROTATION" ]]; then
    bluer_ai_install_module bluer_sbc_screen_rotation 101

    bluer_ai_log "@sbc: screen rotation: $BLUER_SBC_SCREEN_ROTATION"
    if [[ "$abcli_is_rpi" == true ]]; then
        wlr-randr --output HDMI-A-1 --transform $BLUER_SBC_SCREEN_ROTATION
    else
        bluer_ai_log_error "only works on rpi!"
    fi
fi
