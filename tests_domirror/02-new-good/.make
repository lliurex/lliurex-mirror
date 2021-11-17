mkdir -p {lliurex.net/bionic/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/lliurex.net/bionic/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},var}
ln -sr -t . skel/lliurex.net/bionic/dists
ln -sr -t . lliurex.net/bionic/pool/
touch pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211005_all.deb