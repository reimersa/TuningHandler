COUNTER=0

start=$1
end=$2


if [[ $# -ne 2 ]]; then
    echo 
    echo " *** You should specify start and end ***"
    echo 
    exit 2
fi


echo "-----------------------------------"
echo "start runnumber = $start"
echo "end runnumber = $end"
echo "-----------------------------------"

for run in $(seq -f "%06g" $start $end)
do

    # if you want to skip some number, just write it here the if sentence ...
    
    input="Run${run}_NoiseScan.root"
    output="Results_${run}.root"


    if [ ! -f $input ]; then
	echo "!!! $input not found!"
	continue
    fi    

    echo $input, $output
    #root -l -q -b 'copyFiles.C("'${input}'", "'${output}'")'

    let COUNTER=COUNTER+1 
		 
done

#hadd -f combined_${start}_${end}_${COUNTER}.root Results_*.root 
#rm Results_*.root

echo "-----------------------------------"
echo "You added ${COUNTER} files ... you might want to scale your histogram by 1./${COUNTER}"
echo "-----------------------------------"


root -l -b -q 'readoutpixelmap.cxx("'${start}'", "'${end}'", '${COUNTER}')'
