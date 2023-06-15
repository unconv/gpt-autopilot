# GPT-AutoPilot

A GPT-4 powered Python script that can create multi-file projects.

## How to use

1\. Add your [OpenAI API key](https://platform.openai.com/account/api-keys) to a file called `.api_key`

```console
$ echo "YOUR_API_KEY" > .api_key
```

2\. Install the lastest version of the `openai` python package
```console
$ pip install --upgrade openai
```

3\. Run the script. It will ask you for a prompt.

```console
$ ./gpt-autopilot.py
```

4\. For example, tell it to "create a JavaScript inventory application for the browser with a form that can add products with a name, quantity and price. Save the products to localstorage and list them in a table in the application. Calculate the total price of the products in the inventory. Add CSS styles to make the application look professional. Add a Inventory System header and hide the product add form when the page is printed."

5\. The files will be written in the `code/` directory

## Video

Watch the video where I demonstrate how it works here: https://www.youtube.com/watch?v=cnqzTsrdExU

## Support

If you like this code, consider [buying me a coffee](https://buymeacoffee.com/unconv) and/or subscribing to my [YouTube-channel](https://youtube.com/@unconv)
