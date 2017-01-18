# MinutesOfMeeting

This is an example Flock app  https://dev.flock.co/> against the following specifications:
Minutes of the meeting app.

This app is useful to take the minutes of a meeting in any conversation. Your app will provide
the following functionality:

* A Slash command - “mom”
 * /mom start [meeting name] - starts a new meeting. Also ends a previous one if the previous one was not ended
 * /mom stop - stops the current meeting
 * /mom <message> - adds the message to the current meeting minutes
 * /mom list - lists all messages of current meeting
* Side panel, launched from a Launcher button
 * Shows all the minutes in the current chat tab in descending order
 * If no chat tab is open it shows a static message
 
###External Library Requirements
* *pyflock* https://github.com/flockchat/pyflock
* *webapp2*:
 * pip install WebOb
 * pip install Paste
 * pip install webapp2

###To Launch
```sudo python flockapp.py```

__Note__
Current version runs on port 80.
Side panel functionality neds https access.
If https or port 80 access to server is a problem, use ngrok to proxy access <https://ngrok.com/>
