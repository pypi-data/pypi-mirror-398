<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="jp my">

    <!-- 出願人、代理人 -->
    <xsl:template match="jp:m-applicant-and-attorneys">
        <xsl:element name="Applicants">
            <xsl:apply-templates select="jp:m-dispatch-applicant-group" />
        </xsl:element>
        <xsl:element name="Agents">
            <xsl:apply-templates select="jp:m-dispatch-attorney-group" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="jp:m-dispatch-applicant-group | jp:m-dispatch-attorney-group">
        <xsl:variable name="element"
            select="key('dispatched-docs-common-tags-table', local-name(.), $dispatched-docs-common-tags)/@json-key" />
        <xsl:element name="{$element}">
            <xsl:value-of select="my:normalize-name(jp:m-name)" />
        </xsl:element>
    </xsl:template>

    <xsl:key name="dispatched-docs-common-tags-table" match="item" use="@tag" />
    <xsl:variable name="dispatched-docs-common-tags">
        <item tag="m-dispatch-applicant-group" json-key="Applicant" />
        <item tag="m-dispatch-attorney-group" json-key="Agent" />
    </xsl:variable>
</xsl:stylesheet>