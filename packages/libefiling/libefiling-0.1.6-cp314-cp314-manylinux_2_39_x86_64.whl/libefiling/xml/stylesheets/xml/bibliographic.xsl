<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">


    <xsl:template match="/root/procedure-params">
        <xsl:element name="root">
            <xsl:apply-templates select="procedure-param" />
        </xsl:element>
    </xsl:template>

    <!-- 法律種別 -->
    <xsl:template match="procedure-param[@name='law']">
        <xsl:element name="Law">
            <xsl:choose>
                <xsl:when test=". = '1'">patent</xsl:when>
                <xsl:when test=". = '2'">utilityModel</xsl:when>
                <xsl:when test=". = '3'">design</xsl:when>
                <xsl:when test=". = '4'">trademark</xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="." />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <!-- 文書名 -->
    <xsl:template match="procedure-param[@name='document-name']">
        <xsl:element name="DocumentName">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 文書コード -->
    <xsl:template match="procedure-param[@name='document-code']">
        <xsl:element name="DocumentCode">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 出願番号 -->
    <xsl:template
        match="procedure-param[@name='application-number']">
        <xsl:element name="ApplicationNumber">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 登録番号 -->
    <xsl:template
        match="procedure-param[@name='registration-number']">
        <xsl:element name="RegistrationNumber">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 国際出願番号 -->
    <xsl:template
        match="procedure-param[@name='international-application-number']">
        <xsl:element name="InternationalApplicationNumber">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 審判番号 -->
    <xsl:template match="procedure-param[@name='appeal-reference-number']">
        <xsl:element name="AppealReferenceNumber">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 受領番号 -->
    <xsl:template
        match="procedure-param[@name='receipt-number']">
        <xsl:element name="ReceiptNumber">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 整理番号 -->
    <xsl:template
        match="procedure-param[@name='file-reference-id']">
        <xsl:element name="FileReferenceID">
            <xsl:value-of select="." />
        </xsl:element>
    </xsl:template>

    <!-- 提出日(出願日) -->
    <xsl:template
        match="procedure-param[@name='submission-date']">
        <xsl:element name="SubmissionDate">
            <xsl:value-of select="date" />
        </xsl:element>
        <xsl:element name="SubmissionTime">
            <xsl:value-of select="time" />
        </xsl:element>
    </xsl:template>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>
</xsl:stylesheet>