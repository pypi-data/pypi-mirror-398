#! /usr/bin/env bash

function bluer_sbc_parts_adjust() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local generate_grid=$(bluer_ai_option_int "$options" grid 1)

    bluer_ai_eval - \
        python3 -m bluer_sbc.parts \
        adjust \
        --dryrun $do_dryrun \
        --generate_grid $generate_grid \
        "${@:2}"
}
