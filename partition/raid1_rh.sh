#!/bin/bash
########################################################################
#  The parititon script to setup a RAID1  on 
#  Power8LE Server during rhels7.x deployment 
#  
#  The partition script is composed of 2 major logic parts
#  1. select 2 disks on the server to setup the RAID1
#  2. create a partition scheme file /tmp/partitionfile 
########################################################################

########################################################################
# Part 1: select 2 disks available to setup RAID1 
#
########################################################################

# Output the DEVLINKS of disks based on the priority:
# 1 The disk drivers, local disk or remote disk or others
# 2 The disk wwn
# 3 The disk path
# 4 Others

output_file="/tmp/xcat_sorted_disks"
rm -fr $output_file
tmpdir="/tmp/xcat.sorted_disk"
rm -fr $tmpdir
utolcmd="sed -e y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/"
has_awk=$(find /usr/* -name "awk")
tmpdir_for_devlinks="$tmpdir/tmpdir_for_devlinks"
mkdir -p $tmpdir_for_devlinks
tmpfilename_for_sort="$tmpdir/tmpfilename_"

# Get all disk and partitions from /proc/partitions
if [ -z "$has_awk" ]; then
    entries=$(cat /proc/partitions | sed 's/  */ /g' | cut -d " " -f5 | grep -v "name" | grep -e "[s|h|v]d.*$")
else
    entries=$(awk -F ' '  '{print $4}' /proc/partitions | grep -v "name" | grep -e "[s|h|v]d.*$")
fi
# Get disks only with DEVTYPE=disk
for entry in $entries; do     
    udevadm info --query=property --name=/dev/$entry | grep -i "DEVTYPE=disk" > /dev/null
    if [ $? -eq 0 ]; then
        disk_array=$disk_array"$entry "
        echo "[$0] get a disk: $entry"
    fi
done

# Get disk info and sort
for disk in $disk_array; do
    disk_info=$(udevadm info --query=property --name=$disk)
    output_for_wwn=$(IFS= ;echo $disk_info | grep '\<ID_WWN\>' | cut -d "=" -f2)
    disk_wwn=$(echo $output_for_wwn | $utolcmd)
    output_for_path=$(IFS= ;echo $disk_info | grep DEVPATH | cut -d "=" -f2)
    disk_path=$(echo $output_for_path | $utolcmd)
    disk_dev_links=$(IFS= ;echo $disk_info | grep DEVLINKS | cut -d "=" -f2)
    disk_driver=$(udevadm info --attribute-walk --name=$disk | grep DRIVERS| grep -v '""'| grep -v '"sd"'|
                    \head -n 1| sed -e 's/[^"]*"//' -e 's/"//' | $utolcmd)
    
    echo "$disk_dev_links" > "$tmpdir_for_devlinks/$disk"
    # Check whether there is WWN, PATH information
    if [ "$disk_wwn" ]; then
        file_pre="wwn"
        disk_data=$disk_wwn
    elif [ "$disk_path" ]; then
        file_pre="path"
        disk_data=$disk_path
    else
       file_pre="other"
       disk_data=""
    fi
    echo "[$0] disk $disk has $file_pre:$disk_data"
    # Sort disks by DRIVER type
    case "$disk_driver" in
    "ata_piix"*|"pmc maxraid"|"ahci"|"megaraid_sas")
        echo "$disk $disk_data" >> "$tmpfilename_for_sort""$file_pre""firstchoicedisks"
        ;;
    "mptsas"|"mpt2sas"|"mpt3sas")
        echo "$disk $disk_data" >> "$tmpfilename_for_sort""$file_pre""secondchoicedisks"
        ;;
    *)
        echo "$disk $disk_data" >> "$tmpfilename_for_sort""$file_pre""thirdchoicedisks"
        ;;
    esac
done

# The first loop is driver type: first==>second==>third
for driver_type in first second third; do
# The second loop is wwn==>path==>other
    for sort_type in wwn path other; do
        sort_file_name="$tmpfilename_for_sort${sort_type}${driver_type}choicedisks"
        if [ -s "$sort_file_name" ];then
            disks_in_the_file=`cat "$tmpfilename_for_sort${sort_type}${driver_type}choicedisks" | grep -v "^$" | sort -k 2 -b | cut -d " " -f1 | xargs`
            sorted_disk="$sorted_disk$disks_in_the_file "
            echo "[$0] get disk: ($disks_in_the_file) with sort_type:$sort_type"
        fi
    done
done
echo "[$0] the final disk order:"
for disk in $sorted_disk; do
    echo "[$0]       $disk | $(cat $tmpdir_for_devlinks/$disk)"
    echo "$disk|$(cat $tmpdir_for_devlinks/$disk)" >> "$output_file"
done
echo "[$0] the output file is: $output_file"
rm -fr $tmpdir


disk1=$(tail -n +1 /tmp/xcat_sorted_disks|head -n1 |cut -d'|' -f 2|cut -d' ' -f1)
disk2=$(tail -n +2 /tmp/xcat_sorted_disks|head -n1 |cut -d'|' -f 2|cut -d' ' -f1)


########################################################################
# Part 2: create the partition scheme file /tmp/partitionfile
########################################################################
cat > /tmp/partitionfile << EOF
zerombr
clearpart --all
part None --fstype "PPC PReP Boot" --ondisk $disk1 --size 8
part None --fstype "PPC PReP Boot" --ondisk $disk2 --size 8
#Full RAID 1 Sample
part raid.01 --size 512 --ondisk $disk1
part raid.02 --size 512 --ondisk $disk2
raid /boot --level 1 --device md0 raid.01 raid.02
#
part raid.11 --size 1 --grow --ondisk $disk1
part raid.12 --size 1 --grow --ondisk $disk2
raid / --level 1 --device md1 raid.11 raid.12
#
part raid.21 --size 1024 --ondisk $disk1
part raid.22 --size 1024 --ondisk $disk2
raid /var --level 1 --device md2 raid.21 raid.22
#
part raid.31 --size 1024 --ondisk $disk1
part raid.32 --size 1024 --ondisk $disk2
raid swap --level 1 --device md3 raid.31 raid.32

bootloader --boot-drive=$disk1
EOF
