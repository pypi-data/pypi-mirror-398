import logging

class Blogger:
    def __init__(self, logname, loglevel=logging.INFO):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        self.logname = f"{logname}.log"
        logging.basicConfig(filename=self.logname,
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=loglevel)
        logging.info(f"Started log for {logname}")
        self.blog = logging.getLogger(f"{logname}")

    def log(self, msg):
        self.blog.info(msg)

    def send_logs_to_email(self, email="shaman.jaggia@grofers.com"):
        self.__send_mail_to_self(f"Log Report for {self.logname}", email=email, attachement=self.logname)

    @staticmethod
    def __send_mail_to_self(subject, email: str = "shaman.jaggia@grofers.com", attachment=None):
        from_email = "shaman.jaggia@grofers.com"
        to_email = [email]
        subject = subject
        html_content = """<p>Hey,<br><br>
        PFA the log report.<br><br>
        regards,<br>
        jarvis
        <p>"""
        if(attachment is not None):
            pb.send_email(from_email, to_email, subject, html_content,files=[attachment])
        else:
            pb.send_email(from_email, to_email, subject, html_content)