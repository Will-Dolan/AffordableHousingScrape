from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time

def get_zoning(driver, addr: list[str], first_run: bool) -> str:
	zoning = None
	try:
		zoning_url = "https://zimas.lacity.org"
		driver.get(zoning_url)

		if first_run:
			do_not_show = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.ID, "ckDoNotShow"))
			)
			do_not_show.click()
			
			accept = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.ID, "btn"))
			)
			accept.click()

		search_number_box = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, "txtHouseNumber"))
		)
		search_number_box.clear()
		search_number_box.send_keys(addr[0])
		
		search_street_box = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, "txtStreetName"))
		)
		search_street_box.clear()
		search_street_box.send_keys(addr[1])

		search_go = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, "btnSearchGo"))
		)
		search_go.click()
		
		
		time.sleep(2)
		open_zoning = driver.find_element(By.XPATH, '/html/body/form[1]/div[3]/div[3]/div[1]/div/div/table/tbody/tr[7]/td/a')
		open_zoning.click()

		zoning = driver.find_element(By.XPATH, '/html/body/form[1]/div[3]/div[3]/div[1]/div/div/table/tbody/tr[8]/td/div/table/tbody/tr[2]/td[2]/a').text
		
	except Exception as e:
		print(f"An error occurred: {e}")
		
	finally:
		return zoning


def get_dda(driver, addr) -> bool:
	# xpath to popup /html/body/div[1]/main/div/div[4]/div/div[2]/article/div/div/div/div[3]/div/div[2]/div[1]/div[3]/div[2]/div[2]     
	dda = False
	dda_url = 'https://www.huduser.gov/portal/sadda/sadda_qct.html'
	driver.get(dda_url)

	# wait for page to fully load
	time.sleep(1)
	info_2024 = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/div/div[4]/div/div[2]/article/div/div/div/div[3]/div/div[1]/form/fieldset/calcite-radio-button-group/calcite-label[2]'))
	)
	info_2024.click()
	
	search_form = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.CLASS_NAME, 'esri-search__input'))
	)
	search_form.send_keys(addr)
	search_form.send_keys(Keys.RETURN)

	# wait for address to be zoomed in on
	time.sleep(3)
	show_dda = WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/div/div[4]/div/div[2]/article/div/div/div/div[3]/div/div[1]/ul/li[3]/div/div/span[1]/span'))
	)
	show_dda.click()
	
	driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
	time.sleep(0.5) # delay to finish scrolling

	# always runs after resource
	x = -187
	y = -34
	actions = ActionChains(driver)
	actions.move_by_offset(x, y).click().perform()

	try:
		# wait for popup to change
		# TODO: close original popup first
		time.sleep(2) 

		in_dda = WebDriverWait(driver, 2).until(
			EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/main/div/div[4]/div/div[2]/article/div/div/div/div[3]/div/div[2]/div[1]/div[3]/div[2]/div[2]/div[1]/div/calcite-flow/calcite-flow-item/h2'))
		)
		if in_dda.text == 'SADDA Data':
			dda = True
	except Exception as e:
		dda = False
	return dda

def get_resource(driver, addr: str, first_run: bool) -> str:
	resource_level = ''
	try:
		resource_url = 'https://belonging.berkeley.edu/2025-ctcachcd-affh-mapping-tool'
		driver.get(resource_url)

		iframe = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.TAG_NAME, "iframe"))
		)
		driver.switch_to.frame(iframe)
		
		search_box = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'mapboxgl-ctrl-geocoder--input'))
		)
		search_box.clear()
		search_box.send_keys(addr)
		WebDriverWait(driver, 4).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'mapboxgl-ctrl-geocoder--suggestion'))
		)
		search_box.send_keys(Keys.RETURN)


		# wait for zoom
		time.sleep(6)
		x = 610 if first_run else 187
		y = 352 if first_run else 34
		actions = ActionChains(driver)
		actions.move_by_offset(x, y).click().perform()
		time.sleep(5)

		resource_level = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.ID, 'score-name'))
		).text
			
	except Exception as e:
		print(f"An error occurred: {e}")
		
	finally:
		return resource_level


if __name__ == "__main__":
	addrs = ['5455 Wilshire Blvd Los Angeles CA', '2641 Magnolia Ave Los Angeles CA']

	chrome_options = Options()
	''' 
	some notes on the commented lines:
		if headless, I have to set the window size for clicking on the map
		somehow this is slower than not headless. 
	Further todo: I know this is not in the slightest bit optimized, wanted MVP first
				  Will make parallel in the future, run 3 procs for each zoning resource level and dda for each addr 
	'''
	# chrome_options.add_argument("--headless")
	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
	driver.set_window_size(903, 878)

	first_run = True
	for addr in addrs:
		zoning = get_zoning(driver, addr.split(), first_run)
		resource_level = get_resource(driver, addr, first_run)
		dda = get_dda(driver, addr)

		print(f'{addr}\n  Resource level: {resource_level}\n  Zoning: {zoning}\n  DDA: {dda}')
		print()
		first_run = False
	

	driver.quit()
