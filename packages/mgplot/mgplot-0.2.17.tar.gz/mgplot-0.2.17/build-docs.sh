echo " "
echo "About to build the documentation ..."
cd ~/mgplot
rm -rf ./docs
pdoc ./src/mgplot -o ./docs 

