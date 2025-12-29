<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <xsl:template match="/root/jp:pat-app-doc">
        <xsl:element name="root">
            <xsl:apply-templates select=".//jp:inventors" />
            <xsl:apply-templates select=".//jp:applicants" />
            <xsl:apply-templates select=".//jp:agents" />
        </xsl:element>
    </xsl:template>

    <!-- 発明者-->
    <xsl:template match="jp:inventors">
        <xsl:for-each select=".//jp:name">
            <xsl:element name="Inventors">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:for-each>
    </xsl:template>


    <!-- 出願人-->
    <xsl:template match="jp:applicants">
        <xsl:for-each select=".//jp:name">
            <xsl:element name="Applicants">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:for-each>
    </xsl:template>

    <!-- 代理人, 選任した代理人 -->
    <xsl:template match="jp:agents">
        <xsl:for-each select="//jp:agents//jp:name">
            <xsl:element name="Agents">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:for-each>
        <xsl:for-each select="//jp:attorney-change-article//jp:name">
            <xsl:element name="Agents">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:for-each>
    </xsl:template>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>