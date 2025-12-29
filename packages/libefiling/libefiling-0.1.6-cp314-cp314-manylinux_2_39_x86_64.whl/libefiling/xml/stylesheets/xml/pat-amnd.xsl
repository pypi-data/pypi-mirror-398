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
                select="//jp:amendment-a51/jp:applicants |
                        //jp:amendment-a523/jp:applicants |
                        //jp:amendment-a524/jp:applicants |
                        //jp:amendment-a525/jp:applicants |
                        //jp:amendment-a526/jp:applicants |
                        //jp:amendment-a527/jp:applicants |
                        //jp:amendment-a528/jp:applicants |
                        //jp:amendment-a529/jp:applicants |
                        //jp:amendment-a5210/jp:applicants |
                        //jp:amendment-a5211/jp:applicants |
                        //jp:amendment-a5212/jp:applicants" />
             <xsl:apply-templates
                select="//jp:amendment-a51/jp:agents |
                        //jp:amendment-a523/jp:agents |
                        //jp:amendment-a524/jp:agents |
                        //jp:amendment-a525/jp:agents |
                        //jp:amendment-a526/jp:agents |
                        //jp:amendment-a527/jp:agents |
                        //jp:amendment-a528/jp:agents |
                        //jp:amendment-a529/jp:agents |
                        //jp:amendment-a5210/jp:agents |
                        //jp:amendment-a5211/jp:agents |
                        //jp:amendment-a5212/jp:agents" />
            <xsl:apply-templates select=".//jp:amendment-article" />
        </xsl:element>
    </xsl:template>

    <!-- 補正の内容等 -->
    <xsl:template match="jp:amendment-article">
        <xsl:if test="//jp:amendment-article != ''">
            <xsl:element name="Prosecution">
                <xsl:value-of select="my:normalize-text(//jp:amendment-article)" />
            </xsl:element>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
