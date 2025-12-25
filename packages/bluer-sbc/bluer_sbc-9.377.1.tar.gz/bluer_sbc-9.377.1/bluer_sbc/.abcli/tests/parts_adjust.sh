#! /usr/bin/env bash

function test_bluer_sbc_parts_adjust() {
    local options=$1

    [[ "$abcli_is_github_workflow" == true ]] &&
        return 0

    bluer_ai_eval ,$options \
        bluer_sbc_parts_adjust \
        - \
        --verbose 1
}
