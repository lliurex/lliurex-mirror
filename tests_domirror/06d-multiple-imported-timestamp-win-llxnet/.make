mkdir -p {{localhost:1111,localhost:2222,localhost:3333,localhost:4444}/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/{localhost:1111,localhost:2222,localhost:3333,localhost:4444}/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},lliurex.net/bionic/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/lliurex.net/bionic/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},var}
ln -sr -t . skel/lliurex.net/bionic/dists
ln -sr -t . lliurex.net/bionic/pool/
fallocate -l 1M lliurex.net/bionic/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 4M localhost:1111/pool/main/l/lliurex-version-timestamp/file4m.txt
fallocate -l 1M localhost:2222/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 1M localhost:3333/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 1M localhost:4444/pool/main/l/lliurex-version-timestamp/file1m.txt
touch lliurex.net/bionic/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211105_all.deb
touch localhost:1111/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210805_all.deb
touch localhost:2222/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210805_all.deb
touch localhost:3333/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210905_all.deb
touch localhost:4444/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210705_all.deb
