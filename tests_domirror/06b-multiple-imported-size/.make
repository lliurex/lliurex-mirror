mkdir -p {{localhost:1111,localhost:2222,localhost:3333}/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/{localhost:1111,localhost:2222,localhost:3333}/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},lliurex.net/bionic/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/lliurex.net/bionic/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},var}
ln -sr -t . skel/localhost:3333/dists
ln -sr -t . localhost:3333/pool/
fallocate -l 1M lliurex.net/bionic/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 1M localhost:1111/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 4M localhost:2222/pool/main/l/lliurex-version-timestamp/file4m.txt
fallocate -l 2M localhost:3333/pool/main/l/lliurex-version-timestamp/file2m.txt
touch {localhost:1111,localhost:2222,localhost:3333}/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211005_all.deb