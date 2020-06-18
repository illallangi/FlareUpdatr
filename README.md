# FlareUpdatr
[![Docker Pulls](https://img.shields.io/docker/pulls/illallangi/flareupdatr.svg)(https://hub.docker.com/r/illallangi/flareupdatr)
[![Image Size](https://images.microbadger.com/badges/image/illallangi/flareupdatr.svg)(https://microbadger.com/images/illallangi/flareupdatr)
![Build](https://github.com/illallangi/FlareUpdatr/workflows/Build/badge.svg)

Updates CloudFlare DNS entries based on attributes on kubernetes Services.

## Installation

    kubectl apply -f https://raw.githubusercontent.com/illallangi/FlareUpdatr/master/deploy.yaml

Set your cloudflare API key and email address with `kubectl edit -n dns-system cm flareupdatr`.

## Usage

Add the following attributes on a Service object:

    flareupdatr.illallangi.enterprises/domain: example.com

Optionally set the IPIFY URL used with `flareupdatr.illallangi.enterprises/ipify: https://api.ipify.org`.

Override the global Cloudflare settings with:

    flareupdatr.illallangi.enterprises/email
    flareupdatr.illallangi.enterprises/key
