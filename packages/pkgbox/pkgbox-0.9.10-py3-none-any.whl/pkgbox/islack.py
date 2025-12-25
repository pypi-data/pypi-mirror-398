try:
    import pencilbox as pb
except ImportError:
    print("Module not found. Continuing without it.")


class SlackWrapper:
    def __init__(self):
       print('slack wrapper init')

    def send_slack_message(self, channel_id, message=None, file=None, token=None):
        if ((message is not None) and (file is None)):
            try:
                pb.send_slack_message(channel=channel_id, text=message)
                print("*** Slack API worked Fine ***")
            except Exception as e:
                print("*** Slack API Failed ***")
                print("Exeception Error Caught Is: ", e)

        if file is not None:
            message = "PFA" if message is None else message
            try:
                pb.send_slack_message(channel=channel_id, text=message, files=[file])
                print("*** Slack API worked Fine ***")
            except Exception as e:
                print("*** Slack API Failed ***")
                print("Exeception Error Caught Is: ", e)
