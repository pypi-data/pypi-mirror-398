danesmtp () {
        local OPTIND=1 opt
        local -a rrs sigs sslopts
        local rr i=0 host addr usages=23
        local rsa=rsa_pss_rsae_sha256:rsa_pss_rsae_sha384:rsa_pss_rsae_sha512:rsa_pss_pss_sha256:rsa_pss_pss_sha384:rsa_pss_pss_sha512:rsa_pkcs1_sha256:rsa_pkcs1_sha384:rsa_pkcs1_sha512
        local ecdsa=ecdsa_secp256r1_sha256:ecdsa_secp384r1_sha384:ecdsa_secp521r1_sha512

	while getopts a:u:s: opt; do
            case $opt in
                a) addr=$OPTARG
                   case $addr in *:*) addr="[$addr]";; esac;;
                u) usages=$OPTARG;;
                s) case $OPTARG in
                    rsa|RSA) sigs=("-sigalgs" "$rsa" -cipher aRSA);;
                    ecdsa|ECDSA) sigs=("-sigalgs" "$ecdsa" -cipher aECDSA);;
                    *) printf '%s: Only RSA and ECDSA signatures supported\n' "$0"
                       return 1;;
                   esac;;
                *) printf 'usage: danesmtp [-a addr] [-u usages] [-k rsa|ecdsa] host [ssloption ...]\n'
                   return 1;;
            esac
        done
        shift $((OPTIND - 1))
        host=$1
        shift
        if [[ -z "$addr" ]]; then
            addr="$host"
        fi
        sslopts=(-starttls smtp -connect "$addr:25" "${sigs[@]}"
                 -verify 9 -verify_return_error
                 -dane_ee_no_namechecks -dane_tlsa_domain "$host")
        rrs=( $(dig +short +nosplit -t tlsa "_25._tcp.$host" |
                grep -Ei "^[$usages]"' [01] [012] [0-9a-f]+$') )
        while (( i < ${#rrs[@]} - 3 )); do
            rr=${rrs[@]:$i:4}
            i=$((i+4))
            sslopts=("${sslopts[@]}" "-dane_tlsa_rrdata" "$rr")
        done
	echo openssl s_client -brief "${sslopts[@]}" "$@"
        ( sleep 1; printf "QUIT\r\n" ) | openssl s_client -brief "${sslopts[@]}" "$@"
}
