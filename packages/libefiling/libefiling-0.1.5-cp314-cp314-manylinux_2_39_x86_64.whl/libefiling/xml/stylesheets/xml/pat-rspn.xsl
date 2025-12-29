<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="jp">

    <xsl:output method="xml" encoding="utf-8" indent="yes" />
    <xsl:import href="parts/common.xsl" />
    <xsl:import href="parts/submitted-docs.common.xsl" />

    <xsl:template match="/root">
        <xsl:element name="document">
            <xsl:apply-templates select="metadata" />
            <xsl:apply-templates select="procedure-params/procedure-param" />
            <xsl:apply-templates
                select="//jp:response-a53/jp:applicants |
                        //jp:response-a59/jp:applicants" />
            <xsl:apply-templates
                select="//jp:response-a53/jp:agents |
                        //jp:response-a59/jp:agents" />
            <xsl:apply-templates select=".//jp:opinion-contents-article" />
        </xsl:element>
    </xsl:template>

    <!-- 意見の内容等 -->
    <xsl:template match="jp:opinion-contents-article">
        <xsl:if test="//jp:opinion-contents-article != ''">
            <xsl:element name="Prosecution">
                <xsl:value-of select="my:normalize-text(//jp:opinion-contents-article)" />
            </xsl:element>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
 