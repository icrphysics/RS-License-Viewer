"""
Poll raystation license server for details of licenses served 
and parse output into files suitable for display on a users desktop.
"""

import os, re, subprocess
from collections import OrderedDict

# ------------------ #

__Version = 1.107

# ------------------ #

LMX_SERVER = "192.168.146.5"
LMX_PORT = "6200"

# License File to update
TEMP_FILE = 'lic.txt'
# License query utility
LMXENDUTIL = 'lmxendutil.exe'

# License query command with arguments
LMXENDUTIL_ARGS = ['-licstat', '-host',LMX_SERVER, '-port',LMX_PORT, '-network']

# Do not print information for licenses matching any of the following codes
LicenseCodesToIgnore = [
    '8_0_0',        'rayPhotonPhysicsAllMachines',  'rayPhysicsBase',   
    'rayAnatomy',   'rayAdaptive',                  'rayPhotonPhysics',
    'rayOptimizer', 'rayPlatform',                  'rayPlan',
    'rayEvaluation'
    ]

# Even if it matches above do not ignore these licenses
LicenseCodesToProtect = [
    ]

# Change names of the following licenses
LicenseAliasNames = OrderedDict()
LicenseAliasNames['rayStationDoctorBase'] = 'rayDoctor'
LicenseAliasNames['rayStationPlanningBase'] = 'rayPlanning',
    
# Simplify feature names by removing unrequired details from names
stripCodesInFeatureNames = [
    '^7_0_0-Clinical-'
    ]

# Output formatting
COLUMN_1_WIDTH = 30
COLUMN_2_WIDTH = 5

# Number of licenses remaining to trigger an orange flag
LICENSE_ORANGE_LIMIT = 1

# Trigger orange limit on licenses where maximum = 1
TRIGGER_SINGLE_LICENSES = False

# Save Full License Info 
SAVE_FULL_LICENSE_INFO = True
FULL_LICENSE_INFO_FILE = 'FullLicenseInfo.txt'

# Remove duplicate user entries 
# (i.e. where user is connecting to the same feature multiple times)
REMOVE_DUPLICATE_USERS = True

# ------------------ #

# If files are listed with relative paths then prefix path to script
if not os.path.isfile(LMXENDUTIL):
	LMXENDUTIL = os.path.join(os.path.dirname(__file__), LMXENDUTIL)

if not os.path.isfile(TEMP_FILE):
	TEMP_FILE = os.path.join(os.path.dirname(__file__), TEMP_FILE)

if not os.path.isfile(FULL_LICENSE_INFO_FILE):
	FULL_LICENSE_INFO_FILE = os.path.join(os.path.dirname(__file__), FULL_LICENSE_INFO_FILE)

# ------------------ #

def parseLicenseEntry(licenseText):
    """
    Parse individual license text entry and return the feature dictionary 
    The feature dictionary details the feature name, number of licenses used,
    maximum number of licenses available and list of licensed users.
    
    For example license entry like this:
    ----------------------------------------
    Feature: 5_0_2-Clinical-rayArc-3bfdc8531000807a07ad835c2b40fc5d Version: 2.0 Vendor: RAYSEARCHLABS
    Start date: NONE Expire date: 2018-06-01
    Key type: EXCLUSIVE License sharing: HOST 

    1 of 4 license(s) used:
    
    1 license(s) used by blogsj@rayClinicApp01 [192.168.146.20]
        Login time: 2016-06-13 14:56   Checkout time: 2016-06-13 14:56 
        Shared on hostname: rayclinicapp01
    ----------------------------------------
    Return {'Feature':'5_0_2-Clinical-rayArc', 'used':'1', 'maximum':'5', 'users'='blogsj'}
    """

    featureName = None
    numUsed = None
    maxNum = None
    usedBy = []
    
    for licenseLine in licenseText.strip(' -\n\r').split('\n'):
        if 'Feature:' in licenseLine:
            # From: 
            # Feature: 5_0_2-Clinical-rayArc-3bfdc8531000807a07ad835c2b40fc5d Version: 2.0 Vendor: RAYSEARCHLABS
            # Extract: 5_0_2-Clinical-rayArc-3bfdc8531000807a07ad835c2b40fc5d
            featureName = licenseLine.split()[1]
            # From: 5_0_2-Clinical-rayArc-3bfdc8531000807a07ad835c2b40fc5d Extract: 5_0_2-Clinical-rayArc
            featureName = '-'.join(featureName.split('-')[:-1])
        elif 'license(s) used by' in licenseLine:
            # Extract blogsj from:
            # 1 license(s) used by blogsj@rayClinicApp01 [192.168.146.20]
            user = licenseLine.split('license(s) used by')[1].split('@')[0].strip()
            usedBy.append(user)
        elif 'license(s) used' in licenseLine:
            numUsed = licenseLine.split()[0]
            maxNum = licenseLine.split()[2]
    
	if REMOVE_DUPLICATE_USERS:
		usedBy = list(set(usedBy))
	
    return {'Feature':featureName, 'NumUsed':numUsed, 'MaxNum':maxNum, 'Users':usedBy}    

# ------------------ #

def getLicenseInfo(saveOutput=SAVE_FULL_LICENSE_INFO, outFile=FULL_LICENSE_INFO_FILE):
    """
    Use lmxendutil to lookup license server and query license usage for each tool.
    Return list of license information as dictionaries.
    """
    proc = subprocess.Popen([LMXENDUTIL] + LMXENDUTIL_ARGS, stdout=subprocess.PIPE, 
							stderr=subprocess.PIPE)
    out, err = proc.communicate()
    
    licenseDetails = []
    for licenseText in out.split('----------------------------------------')[1:]:
        licenseDetails.append(parseLicenseEntry(licenseText))
    
    if saveOutput:
        with open(outFile,'w') as fp1:
            fp1.write(out)
            
    return licenseDetails
    
# ------------------ #

def filterFeatures(licenseList, ignoreFeatureCodes=[], protectFeatureCodes=[]):
    """
    Filter out uninteresting licenses from the licensed features 
    information list based on feature names.
    Ignoring license feature names matching one of the ignoreFeatureCodes 
    unless they also match one of the protectFeatureCodes.
    """
    newLicenseList = []
    
    for license in licenseList:
        ignoreThisLicense = False
        
        for ignoreCode in ignoreFeatureCodes:
            if ignoreCode in license['Feature']:
                ignoreThisLicense = True
                break
                
        for protectCode in protectFeatureCodes:
            if protectCode in license['Feature']:
                ignoreThisLicense = False
                break
                
        if not ignoreThisLicense:
            newLicenseList.append(license)
             
    return newLicenseList
    
# ------------------ #

def removeLicenseMatches(licenseList1, licenseList2):
    """
    Inplace remove licenses from licenseList1 that are also present in licenseList2
    """
    origFeatures = [license['Feature'] for license in licenseList1]
    for license in licenseList2:
        LicenseInd = origFeatures.index(license['Feature'])
        licenseList1.pop(LicenseInd)
        origFeatures.pop(LicenseInd)

# ------------------ #

def test_removeLicenseMatches():
    """
    Test that we can successfully remove matching licenses
    """

    list1 = [{'Feature':'Feature_1','OtherKey':'Val1'}, {'Feature':'Feature_2','OtherKey':'Val2'}]
    list2 = [{'Feature':'Feature_2','OtherKey':'Val2'}]
    removeLicenseMatches(list1, list2)
    
    assert('Feature_1' in [item['Feature'] for item in list1])
    assert('Feature_2' in [item['Feature'] for item in list2])
    assert('Feature_2' not in [item['Feature'] for item in list1])
    
# ------------------ #

def getRedLicenses(licenseDetails, removeMatches=False):
    """
    Get licenses that are fully used return them in a new dictionary.
    Also optionally remove them from the original dictionary
    """
    newLicenseList = []
    
    for license in licenseDetails:
        if int(license['MaxNum']) == int(license['NumUsed']):
            newLicenseList.append(license)
    
    if removeMatches:
        removeLicenseMatches(licenseDetails, newLicenseList)
        
    return newLicenseList
    
# ------------------ #

def test_getRedLicensesOnly():
    """
    Test that we can retrieve the maximally used licenses
    """

    list1 = [{'Feature':'Feature_1','MaxNum':'5', 'NumUsed':'3'}, {'Feature':'Feature_2','MaxNum':'5', 'NumUsed':'5'}]
    redList = getRedLicenses(list1)
    
    assert('Feature_1' not in [item['Feature'] for item in redList])
    assert('Feature_2' in [item['Feature'] for item in redList])
    
# ------------------ #

def test_getRedAndOtherLicenses():
    """
    Test that we can retrieve the maximally used licenses
    """

    list1 = [{'Feature':'Feature_1','MaxNum':'5', 'NumUsed':'3'}, {'Feature':'Feature_2','MaxNum':'5', 'NumUsed':'5'}]
    redList = getRedLicenses(list1, removeMatches=True)
    
    assert('Feature_1' in [item['Feature'] for item in list1])
    assert('Feature_2' not in [item['Feature'] for item in list1])
    
# ------------------ #

def getOrangeLicenses(licenseDetails, removeMatches=False, orangeThreshold=LICENSE_ORANGE_LIMIT):
    """
    Get licenses that have only orangeThreshold remaining licenses and
    return them in a new dictionary. Also optionally remove them from 
    the original dictionary.
    """
    newLicenseList = []
    
    for license in licenseDetails:
        if (int(license['MaxNum']) - int(license['NumUsed'])) <= orangeThreshold:
            if int(license['MaxNum']) <= orangeThreshold and not TRIGGER_SINGLE_LICENSES:
                continue
            
            newLicenseList.append(license)
            
    if removeMatches:
        removeLicenseMatches(licenseDetails, newLicenseList)
    
    return newLicenseList
    
# ------------------ #
    
def simplifyFeatureNames(licenseDetails, stripCodes=[], replaceCodes=None):
    """
    Go through Feature Names and remove substrings matching items in stripCodes 
    and replace substrings matching keys from replaceCodes with the matching replaceCodes value.
    
    Where stripCodes is a list of regular expression strings
    And replaceCodes is a dictionary of key value pairs where key is a string to 
    search for and value is the string to substitute
    """
    
    for license in licenseDetails:
        for stripCode in stripCodes:
            license['Feature'] = re.sub(stripCode,'',license['Feature'])
    
    if replaceCodes is not None:
        for license in licenseDetails:
            for matchStr, replaceStr in replaceCodes.iteritems():
                print('%s:::%s:%s:::%s' % (license['Feature'], matchStr, replaceStr, re.sub(matchStr, replaceStr, license['Feature'])))
                license['Feature'] = re.sub(matchStr, replaceStr, license['Feature'])
                
# ------------------ #

def writeLicenseInfoFile(filename, licenseDetails):
    """
    Write the license details to a csv file
    """
    with open(filename,'w') as fp1:
        fp1.write('\n%-*s%-*s\t%s\n' % (COLUMN_1_WIDTH, 'Feature', 
                                        COLUMN_2_WIDTH, 'Used', 'Max'))
        for license in licenseDetails:
            fp1.write('%-*s%-*s\t %s\n' % (COLUMN_1_WIDTH, license['Feature'], 
                                            COLUMN_2_WIDTH, license['NumUsed'], 
                                            license['MaxNum']))
            if len(license['Users']) > 0:
                fp1.write('    Used By: %s\n' % (', '.join(license['Users'])))
            fp1.write('\n')

# ------------------ #

def writeLicenseInfo(filename, ignoreFeatureCodes=[], protectFeatureCodes=[], 
                        stripCodes=[], replaceCodes=None, splitByUsage=True):
    """
    Write the list of used license details to one or more csv files removing 
    ignored features and stripping out stripCodes from feature names
    """
    licenseDetails = filterFeatures(getLicenseInfo(), ignoreFeatureCodes=ignoreFeatureCodes, 
                                    protectFeatureCodes=protectFeatureCodes)
    
    simplifyFeatureNames(licenseDetails, stripCodes=stripCodes, replaceCodes=replaceCodes)
    
    if splitByUsage:
        filename = os.path.splitext(filename)[0]
        
        redLicenses = getRedLicenses(licenseDetails, removeMatches=True)
        writeLicenseInfoFile(filename + '.red', redLicenses)
        
        orangeLicenses = getOrangeLicenses(licenseDetails, removeMatches=True)
        writeLicenseInfoFile(filename + '.orange', orangeLicenses)
        writeLicenseInfoFile(filename + '.green', licenseDetails)
    
    else:
        writeLicenseInfoFile(filename, licenseDetails)
    
# ------------------ #

writeLicenseInfo(TEMP_FILE, ignoreFeatureCodes=LicenseCodesToIgnore, 
                    protectFeatureCodes=LicenseCodesToProtect,
                    stripCodes=stripCodesInFeatureNames, replaceCodes=LicenseAliasNames)
