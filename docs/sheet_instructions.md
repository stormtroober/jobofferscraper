# Google Sheets Instructions

## Status Column
The **Status** column allows you to manage the job offers. 

- **CVSENT** (or any other text): 
  - Keep this offer in the list.
  - The scraper will **not** touch it.
  
- **DISCARD**:
  - The next time the scraper runs, this row will be **moved** to the `Trash` worksheet.
  - The job will **not** appear again in the main lists.
  
- **(Empty)**:
  - New offers appear empty.
  - You can leave them empty while reviewing.

## Sorting
- **Newest First**: The scraper grabs the top 50 offers from the website (which are the newest) and adds them to the **top** of your Google Sheet.
- **Top of the list** = Newest offers.
- Old offers are pushed down.
