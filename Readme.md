**Required ENV variables:**  
`DOCUMENTS_FILTER` is additional filter for documents in Paperless. Eg. `type:invoice tag:unpaid`  
`TARGET_TAG_ID` is ID of tag that you want to change  
`FINAL_TAG_ID` is ID of tag you want to change to  
`FIO_TOKEN`  
`PAPERLESS_URL` is URL to Paperless in format `https://paperless-server.com/`  
`PAPERLESS_TOKEN`  
  
Setup:
1. Set `FIO_TOKEN`, `PAPERLESS_URL` and `PAPERLESS_TOKEN`
2. Run the container, switch to cmd
3. `python3 /home/app/main.py fio test`
4. `python3 /home/app/main.py paperless test`
5. `python3 /home/app/main.py paperless tags` to get `TARGET_TAG_ID` and `FINAL_TAG_ID` and optionally slug for filtering  
6. (optional) `python3 /home/app/main.py paperless types` to get slug for filtering
7. Set `DOCUMENTS_FILTER` according to https://docs.paperless-ngx.com/usage/#basic-usage_searching Eg. `type:invoice tag:unpaid`  
8. Edit ENV and run again