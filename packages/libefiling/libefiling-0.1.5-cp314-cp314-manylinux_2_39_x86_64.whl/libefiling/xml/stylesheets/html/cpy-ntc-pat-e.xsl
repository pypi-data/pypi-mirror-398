<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <!-- this xslt was created with reference to cpy-ntc-pat-e.xsl
     of Internet Application Software version i5.30 provided by JPO -->


    <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes"
        doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
        doctype-system="http://www.w3.org/TR/html4/loose.dtd" indent="yes" media-type="text/html" />

    <xsl:include href="parts/v4xva_ntc-pt-e.xsl" />
    <xsl:include href="common.xsl" />

    <!-- lookup table defined in source xml. -->
    <xsl:key name="procedure-params" match="procedure-param" use="@name" />

    <xsl:template match="/root">
        <html>
            <head>
                <title>
                    <xsl:call-template name="html-title">
                        <xsl:with-param name="law"
                            select="/root/procedure-params/procedure-param[@name='law']" />
                        <xsl:with-param name="application-number"
                            select="/root/procedure-params/procedure-param[@name='application-number']" />
                        <xsl:with-param name="document-name"
                            select="/root/procedure-params/procedure-param[@name='document-name']" />
                    </xsl:call-template>
                </title>
                <style>
                    body { font-family: Hiragino Kaku Gothic ProN, Meiryo, Ricty Diminished, Monaco,
                    Consolas,
                    Courier New, Courier, monospace, sans-serif; width: 40em; }
                    p { margin-top: 5px; margin-bottom: 5px; }
                    .dispatch-control-article { font-size: small; }
                    .document-title { text-align: center; font-size: x-large; }
                    .bibliog, .conclusion-part-article, .drafting-body { margin-top: 15px; }
                </style>
            </head>
            <body>
                <xsl:apply-templates select="jp:cpy-notice-pat-exam" />
            </body>
        </html>
    </xsl:template>

    <!-- ====================================================================
     jp:cpy-notice-pat-exam
     ====================================================================-->
    <xsl:template match="jp:cpy-notice-pat-exam">
        <xsl:apply-templates select="jp:dispatch-control-article" />
        <xsl:apply-templates select="jp:notice-pat-exam" />
    </xsl:template>

</xsl:stylesheet>