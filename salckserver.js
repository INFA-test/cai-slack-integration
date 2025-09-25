const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

app.use(bodyParser.json());

const SLACK_BOT_TOKEN = '<token>';
const INFORMATICA_API_URL_TEXT = 'https://.../MainProcess_get_response_slack';   // endpoint for text-only
const INFORMATICA_API_URL_FILE = 'https://.../MainProcess_with_attachment';     // endpoint for messages with files/attachments

app.post('/', async (req, res) => {
  console.log("EVENTTT!");
  const event = req.body;

  // Slack verification
  if (event.type === 'url_verification') {
    return res.json({ challenge: event.challenge });
  }

  // Event callback
  if (event.type === 'event_callback') {
    const message = event.event;

    if (!message.type || message.type === 'app_mention') {
      const messageText = message.text ? message.text.replace(/<[^>]+>/g, '').trim() : '';
      const channelId = message.channel;

      console.log("Message text:", messageText);
      console.log("Channel:", channelId);

      // Check for attachments/files
      const hasAttachment = (message.files && message.files.length > 0) ||
                            (message.attachments && message.attachments.length > 0);

      // Choose endpoint
      const apiUrl = hasAttachment ? INFORMATICA_API_URL_FILE : INFORMATICA_API_URL_TEXT;

      // Build payload
      const informaticaPayload = {
        slack_event_text: messageText,
        slack_channel_id: channelId,
        slack_files: message.files || [],
        slack_attachments: message.attachments || []
      };

      try {
        // Call Informatica process
        const response = await axios.post(apiUrl, informaticaPayload, {
          headers: { 'Content-Type': 'application/json' }
        });

        console.log('Informatica API response:', response.data);

        // Acknowledge back to Slack
        await axios.post('https://slack.com/api/chat.postMessage', {
          channel: channelId,
          text: hasAttachment
            ? `Message + attachment sent to Informatica API`
            : `Message sent to Informatica API`
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

// Server start
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
