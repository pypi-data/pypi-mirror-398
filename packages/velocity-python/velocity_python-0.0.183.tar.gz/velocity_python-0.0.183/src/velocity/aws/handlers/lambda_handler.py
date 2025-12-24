import copy
import json
import os
import pprint
import time
from typing import Optional, Type

from velocity.aws.handlers.base_handler import BaseHandler
from velocity.aws.handlers.response import Response
from velocity.logging import configure_logging, get_logger
from . import context

configure_logging()
logger = get_logger("velocity.aws.handlers.lambda")


class LambdaHandler(BaseHandler):
    user_table: Optional[str] = None
    def __init__(
        self, 
        aws_event, 
        aws_context, 
        context_class: Type[context.Context] = context.Context
    ):
        self.start = time.time()
        super().__init__(aws_event, aws_context, context_class)

        # LambdaHandler-specific initialization
        requestContext = aws_event.get("requestContext") or {}
        identity = requestContext.get("identity") or {}
        headers = aws_event.get("headers") or {}
        auth = identity.get("cognitoAuthenticationProvider")
        self.session = {
            "authentication_provider": identity.get("cognitoAuthenticationProvider"),
            "authentication_type": identity.get("cognitoAuthenticationType"),
            "cognito_user": identity.get("user"),
            "is_desktop": headers.get("CloudFront-Is-Desktop-Viewer") == "true",
            "is_mobile": headers.get("CloudFront-Is-Mobile-Viewer") == "true",
            "is_smart_tv": headers.get("CloudFront-Is-SmartTV-Viewer") == "true",
            "is_tablet": headers.get("CloudFront-Is-Tablet-Viewer") == "true",
            "origin": headers.get("origin"),
            "path": aws_event.get("path"),
            "referer": headers.get("Referer"),
            "source_ip": identity.get("sourceIp"),
            "user_agent": identity.get("userAgent"),
            "sub": auth.split(":")[-1] if auth else None,
        }
        if self.session.get("is_mobile"):
            self.session["device_type"] = "mobile"
        elif self.session.get("is_desktop"):
            self.session["device_type"] = "desktop"
        elif self.session.get("is_tablet"):
            self.session["device_type"] = "tablet"
        elif self.session.get("is_smart_tv"):
            self.session["device_type"] = "smart_tv"
        else:
            self.session["device_type"] = "unknown"


    def beforeAction(self, tx, context):
        # Enhanced activity tracking
        stop_processing = self._enhanced_before_action(tx, context)
        if stop_processing is True:
            return 
        logger.debug("starting LamdaHandler.beforeAction")

        
        self.cognito_user = context.get_cognito_user(self.aws_event)
        self.current_user = {}

        logger.debug("DEBUG: !!! cognito_user %s", self.cognito_user)
        try:
            email_address = self.cognito_user["attributes"]["email"]
            self.session["email_address"] = email_address
        except Exception:
            self.logger.warning("Unable to read email from Cognito user", exc_info=True)

        self.logger.info(
            "Starting action",
            extra={
                "action": context.action(),
                "context_args": context.args(),
                "summary": self._summarize_postdata(context.postdata()),
                "session_email": self.session.get("email_address"),
            },
        )

        if not self.user_table:
            self.logger.warning(
                "user_table not configured; skipping DB lookup for %s",
                self.session.get("email_address"),
            )
            raise Exception(
                "User table not configured; cannot validate user [Config]"
            )
        row = tx.table(self.user_table).find(
            {"email_address": self.session.get("email_address")}
        )
        if not row:
            raise Exception(
                "A valid user with permission is required to access this function [DB]"
            )
        self.current_user = row.to_dict()
         
        temp = copy.deepcopy(context.postdata())
        temp["payload"].pop("cognito_user", None)
        self.logger.debug(
            "Events.OnAction %s",
            temp.get("action"),
            extra={"payload": pprint.pformat(temp)},
        )

    def afterAction(self, tx, context):
        stop_processing = self._enhanced_after_action(tx, context)
        if stop_processing is True:
            return

        logger.debug("starting LamdaHandler.afterAction")

        self.end = time.time()
        self.logger.info(
            "Completed action",
            extra={
                "action": context.action(),
                "duration": self.end - self.start,
            },
        )

    def onError(self, tx, context, exc, tb):
        stop_processing = self._enhanced_error_handler(tx, context, exc, tb)
        if stop_processing is True:
            return
        logger.debug("starting LamdaHandler.aws_api_activity")
        request_id = getattr(self.aws_context, "aws_request_id", None)
        self.logger.error(
            "Unhandled exception for action %s",
            context.action(),
            exc_info=exc,
            extra={"request_id": request_id},
        )

        logger.debug("starting BackOfficeEvents.onError")

        temp = copy.deepcopy(context.postdata())
        logger.debug("starting BackOfficeEvents.log")
        temp["payload"].pop("cognito_user", None)
        self.logger.error(
            "Events.OnError %s",
            temp.get("action"),
            extra={"payload": pprint.pformat(temp), "traceback": tb},
        )
        logger.debug("Ending BackOfficeEvents.OnError Done")
            
    def serve(self, tx):
        response = Response()
        body = self.aws_event.get("body")
        postdata = {}
        if isinstance(body, str) and len(body) > 0:
            try:
                postdata = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                postdata = {"raw_body": body}
        elif isinstance(body, dict):
            postdata = body
        elif isinstance(body, list) and len(body) > 0:
            try:
                new = "\n".join(body)
                postdata = json.loads(new)
            except (json.JSONDecodeError, TypeError):
                postdata = {"raw_body": body}

        req_params = self.aws_event.get("queryStringParameters") or {}
        local_context = self.ContextClass(
            aws_event=self.aws_event,
            aws_context=self.aws_context,
            args=req_params,
            postdata=postdata,
            response=response,
            session=self.session,
            log=lambda message, function=None: self.log(tx, message, function),
        )

        # Determine action from postdata or query parameters
        action = postdata.get("action") or req_params.get("action")
        
        # Get the list of actions to execute
        actions = self.get_actions_to_execute(action)
        
        # Use BaseHandler's execute_actions method
        try:
            self.execute_actions(tx, local_context, actions)
        except Exception as e:
            self.handle_error(tx, local_context, e)
            
        return local_context.response().render()

    def track(self, tx, data=None, user=None, context_obj=None):
        sanitized_payload = context.sanitize_tracking_payload(data or {})
        sanitized_payload.update(
            {
                "source_ip": self.session.get("source_ip"),
                "referer": self.session.get("referer"),
                "user_agent": self.session.get("user_agent"),
                "device_type": self.session.get("device_type"),
            }
        )

        email = context_obj.resolve_tracking_email(user)

        if email:
            sanitized_payload["sys_modified_by"] = email
        elif not sanitized_payload.get("sys_modified_by"):
            sanitized_payload["sys_modified_by"] = self.session.get("email_address") or "system"

        if not email:
            raise Exception(f"Tracking email could not be resolved for tracking.")

        table_name = context_obj.get_tracking_table(email)

        try:
            tx.table(table_name).insert(sanitized_payload)
        except Exception as exc:  # pragma: no cover - best effort logging
            self.log(tx, f"Failed to write tracking record: {exc}", "track")

    def validate(self, user_required=True):
        if user_required:
            try:
                attrs = self.cognito_user["attributes"]
                assert attrs
                assert attrs["email"]
                assert attrs["sub"]
                assert self.session["sub"]
                assert self.session["sub"] == attrs["sub"]
            except:
                raise Exception("User Authentication Error [Cognito]")
        else:
            try:
                if not self.session["sub"]:
                    # User is not signed in. If user_required
                    # is false, then simply return
                    return
                attrs = self.cognito_user["attributes"]
                assert attrs
                assert attrs["email"]
                assert attrs["sub"]
                assert self.session["sub"]
                assert self.session["sub"] == attrs["sub"]
            except:
                raise Exception("User Authentication Error [Cognito]")

    def get_pass_through_vars(self, tx, context):
        """Get pass-through variables: environment vars, layers, and user data"""
        temp = context.get_pass_through_vars(tx, self.current_user)

        logger.debug(
            "LAYER_DEBUG: vars object contains: %s",
            list(temp.get("controls", {}).get("vars", {}).keys()),
        )
        if "layers" in temp.get("controls", {}).get("vars", {}):
            logger.debug(
                "LAYER_DEBUG: layers value: %s",
                temp["controls"]["vars"]["layers"],
            )

        # Merge with user data from database
        temp = context.merge_user_data(tx, temp, self.session["email_address"])

        return temp

    def _summarize_postdata(self, postdata):
        """Extract key fields from postdata for logging without storing entire payload"""
        if not postdata:
            return {}

        summary = {
            "action": postdata.get("action"),
            "payload_keys": (
                list(postdata.get("payload", {}).keys())
                if isinstance(postdata.get("payload"), dict)
                else None
            ),
        }

        # Add size info
        try:
            summary["payload_size_bytes"] = len(json.dumps(postdata.get("payload", {})))
        except:
            summary["payload_size_bytes"] = 0

        return summary