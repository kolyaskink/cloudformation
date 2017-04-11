!/bin/bash

dir="/tmp/jenkinstemp/"
url="git@bitbucket.org:gamehouse-dev/infrajenkins.git"

mkdir $dir && chown jenkins:jenkins $dir
cd $dir && sudo -u jenkins git clone $url
find $dir -not -path '*/\.*' -type f