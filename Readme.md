**Required ENV variables:**  
`TARGET_TYPE_SLUG`  is SLUG of the type you want to search for(for filtering)  
`TARGET_TAG_SLUG` is SLUG of the tag that you want to search forfor filtering)  
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
5. `python3 /home/app/main.py paperless types` to get `TARGET_TYPE_SLUG`
6. `python3 /home/app/main.py paperless tags` to get `TARGET_TAG_SLUG`, `TARGET_TAG_ID` and `FINAL_TAG_ID`
7. Edit ENV and run again