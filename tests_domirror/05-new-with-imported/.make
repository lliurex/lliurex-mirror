mkdir -p {localhost:1111/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/localhost:1111/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},lliurex.net/bionic/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/lliurex.net/bionic/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},var}
ln -sr -t . skel/localhost:1111/dists
ln -sr -t . localhost:1111/pool/
touch pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211005_all.deb