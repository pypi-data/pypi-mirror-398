from TikSign import sign, Newparams, xtoken, trace_id, xor, host, UserAgentTik
import requests




user = input("Enter Any TikTok UserName : ")
params = {
  'id': user,
  'device_platform': "android",
  'os': "android",
  'ssmix': "a",
  '_rticket': "1730473972331",
  'cdid': "b896aa45-f488-486c-8dcf-ede8deffac67",
  'channel': "googleplay",
  'aid': "1233",
  'app_name': "musical_ly",
  'version_code': "370104",
  'version_name': "37.1.4",
  'manifest_version_code': "2023701040",
  'update_version_code': "2023701040",
  'ab_version': "37.1.4",
  'resolution': "1080*2220",
  'dpi': "440",
  'device_type': "Redmi Note 8 Pro",
  'device_brand': "Redmi",
  'language': "ar",
  'os_api': "30",
  'os_version': "11",
  'ac': "mobile",
  'is_pad': "0",
  'current_region': "YE",
  'app_type': "normal",
  'sys_region': "EG",
  'last_install_time': "1730471473",
  'mcc_mnc': "42103",
  'timezone_name': "Asia/Aden",
  'residence': "YE",
  'app_language': "ar",
  'carrier_region': "YE",
  'timezone_offset': "10800",
  'host_abi': "arm64-v8a",
  'locale': "ar",
  'ac2': "lte",
  'uoo': "0",
  'op_region': "YE",
  'build_number': "37.1.4",
  'region': "EG",
  'ts': "1730473972",
  'iid': "7431813370280691461",
  'device_id': "7426861124518282753",
  'openudid': "70301baa15f90dc8"
}
# No Need To Add Something Just Use Newparams()
# Here

params.update(Newparams())

#You Can Use This Function To Get UserAgent And Random Device UserAgent() or UserAgent(params)

ua = UserAgentTik(params)
params.update({'device_type': ua["type"]})
params.update({'device_brand': ua["brand"]})

#You Can Replace the Gorgon Version 0404, 4404, OR Any Version
signature = sign(params=params, payload=None, cookie=None, version="8404")



trace = trace_id() #To Add Arguments In the Headers

headers = {
  'User-Agent': ua["User-Agent"],
  'x-tt-pba-enable': "1",
  'sdk-version': "2",
  'x-tt-dm-status': "login=0;ct=1;rt=7",
  'passport-sdk-version': "6031490",
  'oec-vc-sdk-version': "3.0.4.i18n",
  'x-vc-bdturing-sdk-version': "2.3.8.i18n",
  'x-tt-store-region': "ye",
  'x-tt-store-region-src': "did",
  'rpc-persist-pyxis-policy-v-tnc': "1",
  'x-ss-dp': "1233",
  'x-tt-trace-id': trace,
}
 
headers.update(signature)

api = host() # To Replace The Host Like ( api16-normal-c-alisg.ttapis.com)



response = requests.get(f"https://api16-normal-useast5.tiktokv.us/aweme/v1/user/uniqueid/", params=params, headers=headers)

if "Unique ID is invalid" in response.text:
    print(f"[ # ] - Username Not Found in TikTok : {user}")
elif "uid" in response.text:
    print(f"[ # ] - Username Found in TikTok : {user}")
else:
    print(f"Try To Replace (api16-normal-useast5.tiktokv.us) in Other Host ( {api} )")