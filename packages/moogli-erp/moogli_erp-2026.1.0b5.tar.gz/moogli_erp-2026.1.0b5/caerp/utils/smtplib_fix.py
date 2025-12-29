import base64
from email.base64mime import body_encode as encode_base64
from smtplib import SMTP_SSL, SMTPAuthenticationError, SMTPException

_MAXCHALLENGE = 5


class CustomSMTP(SMTP_SSL):
    def auth(self, mechanism, authobject, *, initial_response_ok=True):
        """Authentication command - requires response processing.

        'mechanism' specifies which authentication mechanism is to
        be used - the valid values are those listed in the 'auth'
        element of 'esmtp_features'.

        'authobject' must be a callable object taking a single argument:

                data = authobject(challenge)

        It will be called to process the server's challenge response; the
        challenge argument it is passed will be a bytes.  It should return
        an ASCII string that will be base64 encoded and sent to the server.

        Keyword arguments:
            - initial_response_ok: Allow sending the RFC 4954 initial-response
            to the AUTH command, if the authentication methods supports it.
        """
        # RFC 4954 allows auth methods to provide an initial response.  Not all
        # methods support it.  By definition, if they return something other
        # than None when challenge is None, then they do.  See issue #15014.
        mechanism = mechanism.upper()
        initial_response = authobject() if initial_response_ok else None
        if initial_response is not None:
            response = encode_base64(initial_response.encode("utf-8"), eol="")
            (code, resp) = self.docmd("AUTH", mechanism + " " + response)
            self._auth_challenge_count = 1
        else:
            (code, resp) = self.docmd("AUTH", mechanism)
            self._auth_challenge_count = 0
        # If server responds with a challenge, send the response.
        while code == 334:
            self._auth_challenge_count += 1
            challenge = base64.decodebytes(resp)
            myauthobject = authobject(challenge)
            if isinstance(myauthobject, str):
                myauthobject = myauthobject.encode("utf-8")
            response = encode_base64(myauthobject, eol="")
            (code, resp) = self.docmd(response)
            # If server keeps sending challenges, something is wrong.
            if self._auth_challenge_count > _MAXCHALLENGE:
                raise SMTPException(
                    "Server AUTH mechanism infinite loop. Last response: "
                    + repr((code, resp))
                )
        if code in (235, 503):
            return (code, resp)
        raise SMTPAuthenticationError(code, resp)
