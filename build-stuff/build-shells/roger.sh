#!/bin/bash

function BuildTrigger {
	case $GitFolder in
		infra-vpc )
  			echo "Roger says - InfraVpc" && \
  			curl -X POST https://127.0.0.1:8080/job/InfraVpc_Deploy_Test/build?token=e0zud9iDkY1cseglsAyg;; 
  		vpc-games )
			echo "Roger says - GamesVpc" && \
			curl -X POST http://127.0.0.1:8080/job/GamesVpc_Tests/build?token=NnT0JdpQUC2URw0tsxwg;; 
		*)
  			sleep 1 ;;
	esac
}



cd $WORKSPACE
git show | grep diff | grep -v grep > ./RogersList

cat ./RogersList | while read Line
do
   GitFolder=$(echo $Line | gawk '{print $4}' | gawk -F/ '{print $2}') && BuildTrigger
done


exit $?
