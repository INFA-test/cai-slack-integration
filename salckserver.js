const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

app.use(bodyParser.json());

const SLACK_BOT_TOKEN = '<token>';
const INFORMATICA_API_URL = 'https://usw1-cai.dmp-us.informaticacloud.com/active-bpel/public/rt/abpTttOyGhYjW2yC5mIze8/MainProcess_get_response_slack';


app.post('/', async (req, res) => {
  console.log("EVENTTT!")
  const event = req.body;
  

  // verification 
  if (event.type === 'url_verification') {
    return res.json({ challenge: event.challenge });
  }

  // real events
  if (event.type === 'event_callback') {
    
    const message = event.event;

    // when bot is mentioned
    if (!message.type || message.type == 'app_mention') {
    //   const messageText = message.text;
      const messageText = message.text.replace(/<[^>]+>/g, '').trim();
      console.log(message.text)
      const channelId = message.channel;
      console.log(channelId)

      // body
      const informaticaPayload = {
        slack_event_text: messageText,
        slack_channel_id:  channelId
      };

      try {
        // CAI procss call
        const response = await axios.post(INFORMATICA_API_URL, informaticaPayload, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        console.log('Informatica API response:', response.data);


        await axios.post('https://slack.com/api/chat.postMessage', {
          text: `Message received and sent to Informatica API: ${messageText}`
        }, {
          headers: {
            'Authorization': `Bearer ${SLACK_BOT_TOKEN}`,
            'Content-Type': 'application/json'
          }
        });

      } catch (error) {
        console.error('Error calling Informatica API:', error.message);
      }
    }
  }

  res.status(200).send();
});

// server start
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
