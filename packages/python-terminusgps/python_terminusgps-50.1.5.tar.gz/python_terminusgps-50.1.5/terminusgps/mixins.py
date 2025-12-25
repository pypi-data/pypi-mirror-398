import typing

from django.http import HttpResponse
from django.views.generic.base import TemplateResponseMixin


class HtmxTemplateResponseMixin(TemplateResponseMixin):
    """
    Renders a partial HTML template depending on HTTP headers.

    `htmx documentation <https://htmx.org/docs/>`_

    """

    partial_template_name: str | None = None
    """
    A partial template rendered by htmx.

    :type: str | None
    :value: None

    """

    def render_to_response(
        self, context: dict[str, typing.Any], **response_kwargs: typing.Any
    ) -> HttpResponse:
        """Sets :py:attr:`template_name` to :py:attr:`partial_template_name` according to request headers."""
        htmx_request = self.request.headers.get("HX-Request", False)
        boosted = self.request.headers.get("HX-Boosted", False)

        if htmx_request and self.partial_template_name and not boosted:
            self.template_name = self.partial_template_name
        return super().render_to_response(context, **response_kwargs)
