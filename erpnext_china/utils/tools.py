
import frappe


def get_doc_or_none(doctype: str, kw: dict):
    # frappe.db.exists 仅会返回找到符合kw条件的第一个
    doc_name = frappe.db.exists(doctype, kw)
    if doc_name:
        doc = frappe.get_doc(doctype, doc_name)
        return doc
    else:
        return None