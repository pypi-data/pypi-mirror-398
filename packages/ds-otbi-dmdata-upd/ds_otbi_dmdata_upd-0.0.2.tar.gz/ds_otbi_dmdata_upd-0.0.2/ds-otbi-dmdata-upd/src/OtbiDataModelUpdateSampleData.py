import re
from playwright.sync_api import Playwright, sync_playwright, expect, Page, BrowserContext, Browser, FrameLocator
from datetime import datetime
import urllib.parse

# Declare URL variables
url = ""
userid = ""
pwd = ""
inp_file = ""

def openInputFile():
    # inp_file = 'ds/TestStream/OtherAutomations/inputfiles/OtbiReportNames.txt'
    try:
        file = open(inp_file, 'r', encoding='utf-8')
        return file
    except FileNotFoundError:
        print(f"Error: The file '{inp_file}' was not found.")

def openLogFile():
    file_path = 'OtbiReportNames-ExecuteDM-StatusLog.txt'
    try:
        file = open(file_path, 'a', encoding='utf-8')
        return file
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")

def loginAndNavigate(playwright: Playwright, logFile) -> tuple:
    # Logs into the system
    browser = playwright.chromium.launch(headless=False, slow_mo=1000, timeout=15000)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)
    page.get_by_role("textbox", name="User Name").click()
    page.get_by_role("textbox", name="User Name").fill(userid)
    page.get_by_role("textbox", name="User Name").press("Tab")
    page.get_by_role("textbox", name="Password").fill(pwd)
    page.get_by_role("button", name="Sign In").click()
    expect(page.get_by_role("link", name="Home", exact=True), "Authentication Error!").to_be_visible(timeout=15000)
    logFile.write("\nSuccessfully logged in!")
    return page, context, browser

def popParamsDefaults(iframeloc: FrameLocator):
    # The below logic tries to understand if there are any date parameters
    # If yes, tries to understand the date format
    # Supplies current date in the format required. 
    try:
        expect(iframeloc.locator("//input[contains(@id, '_params') and @data-paramtype='date']").nth(0), "No date params found").to_be_visible(timeout=10000)
        if iframeloc.locator("//input[contains(@id, '_params') and @data-paramtype='date']").nth(0).is_visible():
            r = 0
            while(r < iframeloc.locator("//input[contains(@id, '_params') and @data-paramtype='date']").count()):
                dtpattern = "%m-%d-%Y"
                get_syspattern = ""
                get_syspattern = iframeloc.locator("//input[contains(@id, '_params') and @data-paramtype='date']").nth(r).get_attribute("data-datepattern")
                if get_syspattern != "":
                    dtpattern = str(get_syspattern).replace('MM', '%m').replace('dd', '%d').replace('yyyy', '%Y')
                iframeloc.locator("//input[contains(@id, '_params') and @data-paramtype='date']").nth(r).fill(datetime.now().strftime(f"{dtpattern}"))
                r = r + 1
    except Exception as e3:
        print ("No date params found or error during param defaulting - ", e3)

def executeDM(page1: Page, dmPath, logFile):
    # Get the DM path. Strip for any blank chars at the end
    dmPath = dmPath.rstrip()
    print("\n\nTrying for " + dmPath)
    logFile.write("\nTrying for " + dmPath)

    # Split the path to enable click by click navigation
    reportNav = dmPath.split("/")

    # Start DM execution
    try:
        # Goto Report Catalog and refresh folder tree to stay at the top
        page1.goto(f"{url}/analytics/saw.dll?catalog")
        page1.get_by_text("Catalog", exact=True).nth(1).click()
        page1.get_by_text("Shared Folders", exact=True).first.click()
        page1.get_by_role("button", name="Refresh").click()

        # Loop through each step in the path to get to the data model
        i = 0
        while i < len(reportNav):
            if reportNav[i] != "":
                # This logic executes once we are at the last of the path i.e., data model name
                if i == len(reportNav) - 1:
                    # Click on Edit Data Model
                    page1.locator(f"a:below(:text(\"{reportNav[i]}\"))").nth(1).click()

                    # Datamodel UI is made up of IFrames. Access the IFrame going forward
                    # Once we hit 'Data' the below logic supplies any date parameters that are required 
                    iframeloc = page1.frame_locator('.ContentIFrame')
                    iframeloc.get_by_text("Data", exact=True).nth(-1).click()
                    popParamsDefaults(iframeloc)
                    iframeloc.get_by_text("View", exact=True).click()
                    page1.wait_for_timeout(2000)

                    # After clicking 'View', updates the sample data by clicking the 'Save as Sample Data' button
                    # The code only waits for 2 mins for the sample data to show up
                    # If not, it logs an error and moves forward to the next data model
                    # For both success and error, it captures the message displayed in the dialog
                    try:
                        expect(iframeloc.locator("//a[@title='Close']").nth(-1)).not_to_be_visible()
                        # Try for 120s
                        elapsed = 0
                        while elapsed <= 120:
                            if iframeloc.get_by_text("Save As Sample Data", exact=True).is_enabled():
                                iframeloc.get_by_text("Save As Sample Data", exact=True).click()
                                msg = iframeloc.locator('#md2_dialogBody').inner_text()
                                iframeloc.locator("//button[text()='OK']").nth(-1).click()
                                logFile.write(f" - Success ({msg})")
                                break
                            else:
                                if elapsed == 120:
                                    logFile.write(f" - Error. Processing beyond 2 mins")
                                page1.wait_for_timeout(5000)
                                elapsed = elapsed + 5
                    except Exception as e2:
                        print ("Error during DM execution - ", e2)
                        msg = iframeloc.locator('#md2_dialogBody').inner_text()
                        logFile.write(f" - Execution Error ({msg})")
                        iframeloc.locator("//a[@title='Close']").nth(-1).click()
                        break
                else:
                    # Click on the folder tree and keep proceeding to the next one
                    page1.get_by_text(f"{reportNav[i]}", exact=True).first.dblclick()
            i = i + 1
        
        # page1.close()
    except Exception as e1:
        print ("Error during DM navigate - ", e1)
        logFile.write(" - Unable to initial data model execution or data model not found")

def closeBrowser(context: BrowserContext, browser: Browser):
    context.close()
    browser.close()

def run(playwright: Playwright) -> None:
    # Open Input and Log Files
    # Input file should contain path to data models without the '/' at the start
    inpFile = openInputFile()
    logFile = openLogFile()
    logFile.write("\n") # type: ignore
    logFile.write(f"\nExecution started on {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}") # type: ignore

    # Get Browser Session
    pg, cntxt, brwsr = loginAndNavigate(playwright, logFile)

    # Loop through each of the data model in the input file
    if inpFile:
        for line in inpFile:
            executeDM(pg, line, logFile)

    # Close and wrap-up
    closeBrowser(cntxt, brwsr)
    logFile.write(f"\nExecution ended on {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}") # type: ignore
    logFile.write("Check log in your current directory. Log Name - OtbiReportNames-ExecuteDM-StatusLog.txt") # type: ignore
    inpFile.close() # type: ignore
    logFile.close() # type: ignore


with sync_playwright() as playwright:
    # Get instance and credentials
    url = input("Enter the URL of the Oracle Instance ending with '.com' (no slashes) - ")
    userid = input("Enter the User ID - ")
    pwd = input("Enter the password - ")
    inp_file = input("Enter the filename with the path containing the listing of data models - ")

    # Begin Execution
    run(playwright)
