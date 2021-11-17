mkdir -p {{localhost:1111,localhost:2222,localhost:3333}/pool/{main,universe,multiverse}/l/lliurex-version-timestamp,skel/{localhost:1111,localhost:2222,localhost:3333}/dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse},pool/{main,universe,multiverse}/l/lliurex-version-timestamp,var,dists/{bionic,bionic-updates,bionic-security}/{main,universe,multiverse}}
#ln -sr -t . skel/localhost:3333/dists
#ln -sr -t . localhost:3333/pool/
fallocate -l 1M pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 4M localhost:1111/pool/main/l/lliurex-version-timestamp/file4m.txt
fallocate -l 1M localhost:2222/pool/main/l/lliurex-version-timestamp/file1m.txt
fallocate -l 1M localhost:3333/pool/main/l/lliurex-version-timestamp/file1m.txt
touch pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210705_all.deb
touch localhost:1111/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210805_all.deb
touch localhost:2222/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.211005_all.deb
touch localhost:3333/pool/main/l/lliurex-version-timestamp/lliurex-version-timestamp_19.210905_all.deb