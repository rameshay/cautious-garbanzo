#!/bin/bash

#
# manipulate IPSec SA database on behalf of the racoon daemon
# Gabriel Somlo <somlo at cmu edu>, 08/27/2007
#

#FIXME: read this from, e.g., /etc/sysconfig/racoon
NAT_T="yes"


shopt -s nocasematch
umask 0022

PATH=/bin:/sbin:/usr/bin:/usr/sbin

# set up NAT-T
case "${NAT_T}" in
  yes|true|on|enable*|1)
    LOCAL="${LOCAL_ADDR}[${LOCAL_PORT}]"
    REMOTE="${REMOTE_ADDR}[${REMOTE_PORT}]"
    ;;
  *)
    LOCAL="${LOCAL_ADDR}"
    REMOTE="${REMOTE_ADDR}"
    ;;
esac

# determine interface and next-hop for our default route
DFLT_RT=$(ip route list | awk '($1 == "default"){print $3 ";" $5}')
DFLT_IF=${DFLT_RT#*;}
DFLT_GW=${DFLT_RT%;*}


# bring down phase1
phase1_down() {
  # restore previous resolv.conf
  [ -f /etc/resolv.conf.prevpn ] && mv /etc/resolv.conf.prevpn /etc/resolv.conf

  if [ -n "${SPLIT_INCLUDE_CIDR}" ]; then
    # split tunnel: remove specific tunnel routes
    for N in ${SPLIT_INCLUDE_CIDR}; do
      ip route del ${N}
    done
  else
    # full tunnel: remove any applicable exceptions
    for N in ${SPLIT_LOCAL_CIDR}; do
      ip route del ${N}
    done
    # ... then restore original default route
    ip route del default
    ip route add default via ${DFLT_GW} dev ${DFLT_IF}
  fi

  # remove host route to VPN server
  ip route del ${REMOTE_ADDR}
  # remove VPN address from default interface
  ip addr del dev ${DFLT_IF} ${INTERNAL_ADDR4}/32

  # clean up SA database
  setkey -c << EOT
spddelete ${INTERNAL_ADDR4}/32[any] 0.0.0.0/0[any] any -P out ipsec
          esp/tunnel/${LOCAL}-${REMOTE}/require;
spddelete 0.0.0.0/0[any] ${INTERNAL_ADDR4}[any] any -P in ipsec
          esp/tunnel/${REMOTE}-${LOCAL}/require;
deleteall ${REMOTE_ADDR} ${LOCAL_ADDR} esp;
deleteall ${LOCAL_ADDR} ${REMOTE_ADDR} esp; 
# deleteall still broken on Linux, using 'flush esp' as workaround:
flush esp;
EOT
}


# print out parameters we received
echo "p1_up_down: $1 starting..."
echo "p1_up_down: LOCAL_ADDR = ${LOCAL_ADDR}"
echo "p1_up_down: LOCAL_PORT = ${LOCAL_PORT}"
echo "p1_up_down: REMOTE_ADDR = ${REMOTE_ADDR}"
echo "p1_up_down: REMOTE_PORT = ${REMOTE_PORT}"
echo "p1_up_down: DFLT_GW = ${DFLT_GW}"
echo "p1_up_down: DFLT_IF = ${DFLT_IF}"
echo "p1_up_down: INTERNAL_ADDR4 = ${INTERNAL_ADDR4}"
echo "p1_up_down: INTERNAL_DNS4 = ${INTERNAL_DNS4}"
echo "p1_up_down: DEFAULT_DOMAIN = ${DEFAULT_DOMAIN}"
echo "p1_up_down: SPLIT_INCLUDE_CIDR = ${SPLIT_INCLUDE_CIDR}"
echo "p1_up_down: SPLIT_LOCAL_CIDR = ${SPLIT_LOCAL_CIDR}"

# check for valid VPN address
echo ${INTERNAL_ADDR4} | grep -q '[0-9]' || {
  echo "p1_up_down: error: invalid INTERNAL_ADDR4."
  exit 1
}

# check for valid default nexthop
echo ${DFLT_GW} | grep -q '[0-9]' || {
  echo "p1_up_down: error: invalid DFLT_GW."
  exit 2
}

phase1_down
exit 0
