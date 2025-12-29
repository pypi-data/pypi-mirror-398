<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="my jp">

    <xsl:output method="xml" encoding="utf-8" indent="yes" />
    <xsl:import href="parts/common.xsl" />
    <xsl:import href="parts/submitted-docs.common.xsl" />

    <xsl:template match="/root">
        <xsl:element name="document">
            <xsl:element name="IsForeignLanguage">
                <xsl:value-of select="true()" />
            </xsl:element>
            <xsl:apply-templates select="metadata" />
            <xsl:apply-templates select="procedure-params/procedure-param" />
            <xsl:apply-templates select=".//jp:inventors" />
            <xsl:apply-templates select=".//jp:applicants" />
            <xsl:apply-templates select=".//agents" />
            <xsl:apply-templates select="jp:foreign-language-body/jp:foreign-language-claims" />
            <xsl:apply-templates select="jp:foreign-language-body/jp:foreign-language-description" />
            <xsl:apply-templates select="jp:foreign-language-body/jp:foreign-language-abstract" />
        </xsl:element>
    </xsl:template>

    <!-- lookup <images> in source xml -->
    <xsl:key name="image-table" match="images/image[@size_tag='large']" use="@orig" />

    <!-- 明細書全文 -->
    <xsl:template match="jp:foreign-language-description">
        <xsl:element name="Description">
            <xsl:call-template name="ocr" />
        </xsl:element>
    </xsl:template>

    <!-- 要約書 -->
    <xsl:template match="jp:foreign-language-abstract">
        <xsl:element name="Abstract">
            <xsl:call-template name="ocr" />
        </xsl:element>
    </xsl:template>

    <!-- 請求項 -->
    <xsl:template match="jp:foreign-language-claims">
        <xsl:element name="IndependentClaims">
            <xsl:call-template name="ocr" />
        </xsl:element>
    </xsl:template>

    <xsl:template name="ocr">
        <xsl:for-each select=".//img">
            <xsl:variable name="file-name" select="key('image-table', @file)[1]" />
            <xsl:variable name="new-file-name" select="$file-name/@new" />
            <xsl:variable name="ocr-text" select="//ocr-text/text[@src-image=$new-file-name]" />
            <xsl:value-of select="$ocr-text" />
        </xsl:for-each>
    </xsl:template>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>