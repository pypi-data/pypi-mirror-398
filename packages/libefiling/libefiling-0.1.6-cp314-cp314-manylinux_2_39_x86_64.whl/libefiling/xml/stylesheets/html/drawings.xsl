<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    exclude-result-prefixes="jp">

    <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes" indent="yes"
        media-type="text/html" />

    <xsl:variable name="node" select="name(//jp:pat-app-doc/*)" />
    <xsl:variable name="kind-of-law" select="//jp:pat-app-doc/*/@jp:kind-of-law" />

    <xsl:include href="parts/pat_common.xsl" />

    <!-- lookup table defined in source xml. -->
    <xsl:key name="procedure-params" match="procedure-param" use="@name" />

    <xsl:template match="/root">
        <xsl:element name="div">
            <xsl:apply-templates select="application-body/drawings" />
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>