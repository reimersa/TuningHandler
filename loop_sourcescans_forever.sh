#!/bin/bash
i="0"
while [ $i -lt 1 ]
do
    CMSITminiDAQ -f xml/CMSIT_singleQuad_modT04_source.xml -c noise
    sleep 5
done
