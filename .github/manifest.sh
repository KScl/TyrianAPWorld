manifest_ver=7
manifest_compat_ver=7
world_ver=${1:1}

verinfo="\"version\": $manifest_ver, \"compatible_version\": $manifest_compat_ver, "
worldinfo=", \"world_version\": \"$world_ver\""
json=`cat archipelago.json`
json="${json/\{/\{$verinfo}"
json="${json/\}/$worldinfo\}}"
echo $json > archipelago.json
