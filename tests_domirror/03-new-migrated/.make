mkdir -p {lliurex.net/bionic/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/lliurex.net/bionic/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},var,old_dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse}}
ln -sr -t . skel/lliurex.net/bionic/dists
ln -sr -t . lliurex.net/bionic/pool/
touch pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211005_all.deb
touch old_dists/bionic/main/old_dummy.gz
touch pool/main/l/lliurex-version-timestamp/old_lliurex-version-timestamp_19.200105_all.deb