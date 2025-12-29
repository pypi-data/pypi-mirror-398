<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp"
    xmlns:my="my"
    exclude-result-prefixes="my">

    <xsl:import href="common-templates/common.xsl" />
    <xsl:import href="sub-templates/submitted-docs.common.xsl" />

    <xsl:template match="/">
        <xsl:element name="root">
            <xsl:apply-templates select="root/application-body/description" />
            <xsl:apply-templates select="root/application-body/claims" />
            <xsl:apply-templates select="root/application-body/abstract" />
        </xsl:element>
    </xsl:template>

    <!-- 明細書 -->
    <xsl:template name="description">
        <xsl:apply-templates />
    </xsl:template>

    <!-- 発明/考案の名称, 技術分野, 背景技術, 解決しようとする課題, 解決手段、
         効果, 実施形態, 産業上の利用可能性 -->
    <xsl:template
        match="
        invention-title | technical-field | background-art |
        tech-problem | tech-solution | advantageous-effects |
        description-of-embodiments | industrial-applicability">
        <xsl:variable name="element"
            select="key('tags-table-key', name(.), $tags-table)/@json-key" />
        <xsl:element name="{$element}">
            <xsl:value-of select="normalize-space(.)" />
        </xsl:element>
    </xsl:template>

    <!-- 要約書 -->
    <xsl:template match="abstract">
        <xsl:element name="Abstract">
            <xsl:value-of select="my:normalize-text(//abstract)" />
        </xsl:element>
    </xsl:template>

    <!-- 請求項 -->
    <xsl:template match="claims">
        <xsl:element name="DependentClaims">
            <xsl:for-each select="claim[contains(claim-text,'請求項')]">
                <!-- <xsl:value-of select="my:normalize-text(.)" /> -->
                <xsl:value-of select="normalize-space(.)" />
            </xsl:for-each>
        </xsl:element>
        <xsl:element name="IndependentClaims">
            <xsl:for-each select="claim[not(contains(claim-text,'請求項'))]">
                <xsl:value-of select="normalize-space(.)" />
            </xsl:for-each>
        </xsl:element>
    </xsl:template>

    <xsl:key name="tags-table-key" match="item" use="@tag" />
    <xsl:variable name="tags-table">
        <item tag="applicants" json-key="Applicants" />
        <item tag="inventors" json-key="Inventors" />
        <item tag="invention-title" json-key="InventionTitle" />
        <item tag="technical-field" json-key="TechnicalField" />
        <item tag="background-art" json-key="BackgroundArt" />
        <item tag="tech-problem" json-key="TechProblem" />
        <item tag="tech-solution" json-key="TechSolution" />
        <item tag="advantageous-effects" json-key="AdvantageousEffects" />
        <item tag="description-of-embodiments" json-key="Embodiments" />
        <item tag="industrial-applicability" json-key="IndustrialApplicability" />
        <item tag="description" json-key="Description" />
    </xsl:variable>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>