'''
Your task is to write a Python program to do the following:

  1) Access the first page of results for health inspection information from the Napa County health department website.

  2) Access each inspection of each facility on that page and collect the following information:
     - Facility name
     - Street address
     - City
     - State
     - ZIP code
     - Inspection date
     - Inspection type
     - Inspection grade
     - Item number and description for each out-of-compliance violation

     * For example, violation item number 6 has the description "Adequate handwashing facilities supplied & accessible"

  3) Create a JSON structure to store the collected information, and write that JSON structure to disk.

  4) Print the collected information to the console in an easy-to-understand format.

'''


import json, requests, re
from bs4 import BeautifulSoup


'''
Change between page results by editing the "start=xx" in the url
Pages are displayed in 10s -- first page "start=1" .. =11 .. =21
'''
page_url = (
  "http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=03/01/2017&kw1=&kw2=&kw3="
  "&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar"
)

output = {}    # dict object that will be converted to json


def main():
  # first verify 200 code response 
  try:
    print('Attempting request: ', page_url)
    page = requests.get(page_url)
  except requests.exceptions.RequestException as e:
    print(e)
    return
  
  
  '''
  Variable initializations:
  '''
  foundResultsStart = False      # bool indicating whether we found the start of the pertinent data
  foundTableStart = False        # bool indicating whether we found the start of the pertinent data
  targetData = []         # list containing pertinent data 
  inspectionURLs = []     # list containing urls for specific inspection data 
  inspectionReports = []  # list containing each report GET request response data 
  segmentCount = 8        # lines pertaining to one facility 
  index = 0               # keep count of lines  
  currentFacility = 0     # iterate every 8 lines 


  '''
  Narrow down specific response data that we are targeting:
  '''
  soupParsedContent = BeautifulSoup(page.content, 'html.parser')
  htmlContent = list(soupParsedContent.children)[3]   # html data from page request
  searchResults = list(htmlContent.children)[3]       # data specific to this page results


  '''
  Get URLs to proceed to detailed inspection results
  Need to perform 10 additional GET requests as per the 10 responses per search 
  '''
  for value in searchResults.find_all('a', href=True, text=True):
    if "report_full" in value['href']:
      inspectionURLs.append('http://ca.healthinspections.us'+value['href'][2:])
  for value in inspectionURLs:
    try:
      print('Attempting request: ', value)
      reportPage = requests.get(value)
      inspectionReports.append(reportPage)
    except requests.exceptions.RequestException as e:
      print(e)
      continue

  
  '''
  Once detailed inspection link is saved, begin parsing the stripped html 
    of the original requested page for basic information
  '''
  for value in searchResults.stripped_strings:
    if foundResultsStart == False:
      if "Displaying results" in value:
        foundResultsStart = True;
      continue
    if "Result Pages" in value:
      break                         
    targetData.append(value) 


  '''
  From the targetData list, we can begin writing to our dict with the data 
    found on each facility
  '''
  for value in targetData:
    if (((index) % segmentCount) == 0):   # found start of new facility data
      currentFacility += 1
      output[currentFacility] = {}        # init current facility index in dict, create new format  
      output[currentFacility]['facilityName'] = value 
      output[currentFacility]['streetAddress'] = ''
      output[currentFacility]['city'] = ''
      output[currentFacility]['state'] = ''
      output[currentFacility]['zip'] = ''
      output[currentFacility]['inspectionDate'] = ''
      output[currentFacility]['inspectionType'] = ''
      output[currentFacility]['inspectionGrade'] = ''
      output[currentFacility]['violationItems'] = {}

      '''
      Perform detailed inspection report on this facility, store in 'violationItems'
      '''
      soupParsedReports = BeautifulSoup(inspectionReports[currentFacility-1].content, 'html.parser')
      for innerTable in soupParsedReports.find_all("table", {"class": "insideTable"}): 
        violationItemsCount = 1
        for tableRow in innerTable.find_all("tr", {"class": None}):
          for row in tableRow.find_all('td')[2]:
            if "box_unchecked" in row['src']:
              continue
            for rule in tableRow.find_all('td')[0]:
              output[currentFacility]['violationItems'][violationItemsCount] = rule
              violationItemsCount += 1

    '''
    Retrieve rest of data from initially requested page 
    '''
    if (((index) % segmentCount) == 2):   # found permit type
      output[currentFacility]['inspectionType'] = value
    if (((index) % segmentCount) == 3):   # found st. address
      output[currentFacility]['streetAddress'] = value
    if (((index) % segmentCount) == 4):   # found city, state, and zip
      output[currentFacility]['city'] = value.split(',', 1)[0]
      stateAndZip = value.split(',', 1)[1]
      output[currentFacility]['state'] =  stateAndZip.split()[0] 
      output[currentFacility]['zip'] = stateAndZip.split()[1]
    if (((index) % segmentCount) == 6):   # found last insp. date
      output[currentFacility]['inspectionDate'] = value
    if (((index) % segmentCount) == 7):   # found insp. grade
      output[currentFacility]['inspectionGrade'] = value.strip()[-1]
    index += 1


'''
Call main func and write results to command line as well as to 
  the data.txt created at current directory
'''
if __name__ == '__main__':
  main()
  print(json.dumps(output, indent=3, sort_keys=True))
  with open('data.json', 'w') as outfile:  
    json.dump(output, outfile, indent=3, sort_keys=True)
