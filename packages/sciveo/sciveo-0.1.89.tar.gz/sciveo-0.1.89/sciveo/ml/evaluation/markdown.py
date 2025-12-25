#
# Stanislav Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact s.georgiev@softel.bg.
#
# 2025
#

import re
import difflib
from collections import defaultdict


class EvalMarkdownSimple:
  def __init__(self, md_true: str, md_predicted: str, similarity_threshold=0.8):
    self.md_true = md_true.split("\n")
    self.md_predicted = md_predicted.split("\n")
    self.similarity_threshold = similarity_threshold
    self.results = {"EM": [], "PM": [], "FN": [], "FP": [], "RI": [], "H": [], "FE": []}

  def _find_best_match(self, text, candidates):
    """
    Finds the best matching text block from predicted Markdown using similarity comparison.

    :param text: The labeled Markdown text to match.
    :param candidates: The list of LLM-generated Markdown text blocks.
    :return: (best_match, similarity_score) or (None, 0) if no match found.
    """
    best_match = None
    best_score = 0
    text_lower = text.lower()

    for candidate in candidates:
      score = difflib.SequenceMatcher(None, text_lower, candidate.lower()).ratio()
      if score > best_score:
        best_score = score
        best_match = candidate

    return (best_match, best_score) if best_score >= self.similarity_threshold else (None, 0)

  def _check_formatting_errors(self, original, predicted):
    """
    Checks for incorrect Markdown formatting in predicted text.

    :param original: The manually labeled Markdown text.
    :param predicted: The LLM-generated Markdown text.
    :return: True if formatting errors exist, False otherwise.
    """
    # Basic check: header formatting, bold/italic differences
    if original.strip("#*`").strip() == predicted.strip("#*`").strip():
      return True
    return False

  def evaluate(self):
    """
    Evaluates Markdown
    """
    matched_predicted_blocks = set()
    predicted_idx_map = {block: idx for idx, block in enumerate(self.md_predicted)}

    for true_text in self.md_true:
      best_match, score = self._find_best_match(true_text, self.md_predicted)

      if best_match:
        matched_predicted_blocks.add(best_match)
        if score == 1.0:
          self.results["EM"].append((true_text, best_match))
        else:
          self.results["PM"].append((true_text, best_match, score))

        # Check for formatting errors
        if self._check_formatting_errors(true_text, best_match):
          self.results["FE"].append((true_text, best_match))
      else:
        self.results["FN"].append(true_text)

    # False Positives (extra predicted blocks that don't match labeled Markdown)
    for pred_text in self.md_predicted:
      if pred_text not in matched_predicted_blocks:
        self.results["FP"].append(pred_text)

    # Check for hallucinations (predicted content not in labeled text)
    for pred_text in self.results["FP"]:
      best_match, _ = self._find_best_match(pred_text, self.md_true)
      if best_match is None:
        self.results["H"].append(pred_text)

    # Check for order issues (text found but misordered)
    true_texts = [t for t, _ in self.results["EM"]] + [t for t, _, _ in self.results["PM"]]
    pred_texts = [p for _, p in self.results["EM"]] + [p for _, p, _ in self.results["PM"]]

    true_indices = [predicted_idx_map[text] for text in pred_texts if text in predicted_idx_map]
    if true_indices != sorted(true_indices):
      self.results["RI"].append(true_indices)

    return self.results

  def score(self):
    """
    Computes an improved similarity score with weighted Partial Matches (PM).
    """
    TP = len(self.results["EM"])
    PM_weighted = sum(score for _, _, score in self.results["PM"])
    FN = len(self.results["FN"])
    FP = len(self.results["FP"])

    precision = (TP + PM_weighted) / (TP + PM_weighted + FP) if (TP + PM_weighted + FP) > 0 else 0
    recall = (TP + PM_weighted) / (TP + PM_weighted + FN) if (TP + PM_weighted + FN) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {"Precision": precision, "Recall": recall, "F1 Score": f1_score}


class EvalMarkdown:
  def __init__(self, md_true, md_predicted):
    """
    Evaluates labeled (true) Markdown against predicted Markdown with section-wise evaluation.
    """
    self.md_true = self._parse_markdown(md_true.lower())
    self.md_predicted = self._parse_markdown(md_predicted.lower())
    self.results = defaultdict(lambda: {"EM": [], "PM": [], "FN": [], "FP": []})

  def _parse_markdown(self, markdown_text):
    """
    Parses Markdown into a dictionary of sections where key = heading, value = list of text blocks.
    """
    sections = defaultdict(list)
    current_section = "INTRO"  # Default section if no heading appears

    for line in markdown_text.split("\n"):
      heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
      if heading_match:
        current_section = heading_match.group(2).strip()  # Extract section title
      else:
        if line.strip():
          sections[current_section].append(line.strip())

    return sections

  def _find_best_match(self, text, true_texts):
    """
    Finds the best match for a given text within a list of true texts.
    Returns (best_match_text, similarity_score).
    """
    if not true_texts:
      return None, 0

    from difflib import SequenceMatcher
    best_match, best_score = None, 0

    for true_text in true_texts:
      score = SequenceMatcher(None, text, true_text).ratio()
      if score > best_score:
        best_match, best_score = true_text, score

    return best_match, best_score

  def evaluate(self):
    all_sections = set(self.md_true.keys()).union(set(self.md_predicted.keys()))
    for section in all_sections:
      true_texts = self.md_true.get(section, [])
      pred_texts = self.md_predicted.get(section, [])

      matched_true = set()
      matched_pred = set()

      # Exact matches
      for pred_text in pred_texts:
        if pred_text in true_texts:
          self.results[section]["EM"].append((pred_text, pred_text))
          matched_true.add(pred_text)
          matched_pred.add(pred_text)

      # Partial matches
      for pred_text in pred_texts:
        if pred_text not in matched_pred:
          best_match, score = self._find_best_match(pred_text, true_texts)
          if best_match and score > 0.8:  # Accept only good matches
            self.results[section]["PM"].append((best_match, pred_text, score))
            matched_true.add(best_match)
            matched_pred.add(pred_text)

      # False negatives (missed text from ground truth)
      for true_text in true_texts:
        if true_text not in matched_true:
          self.results[section]["FN"].append(true_text)

      # False positives (extra predicted text)
      for pred_text in pred_texts:
        if pred_text not in matched_pred:
          self.results[section]["FP"].append(pred_text)

    return self.results

  def score(self):
    """
    Computes section-wise and global similarity scores.
    """
    section_scores = {}
    global_TP, global_PM, global_FN, global_FP = 0, 0, 0, 0

    for section, result in self.results.items():
      TP = len(result["EM"])
      PM_weighted = sum(score for _, _, score in result["PM"])
      FN = len(result["FN"])
      FP = len(result["FP"])

      precision = (TP + PM_weighted) / (TP + PM_weighted + FP) if (TP + PM_weighted + FP) > 0 else 0
      recall = (TP + PM_weighted) / (TP + PM_weighted + FN) if (TP + PM_weighted + FN) > 0 else 0
      f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

      section_scores[section] = {"Precision": precision, "Recall": recall, "F1 Score": f1_score}

      global_TP += TP
      global_PM += PM_weighted
      global_FN += FN
      global_FP += FP

    # Global precision/recall across all sections
    global_precision = (global_TP + global_PM) / (global_TP + global_PM + global_FP) if (global_TP + global_PM + global_FP) > 0 else 0
    global_recall = (global_TP + global_PM) / (global_TP + global_PM + global_FN) if (global_TP + global_PM + global_FN) > 0 else 0
    global_f1 = (2 * global_precision * global_recall) / (global_precision + global_recall) if (global_precision + global_recall) > 0 else 0

    return {"Sections": section_scores, "Global": {"Precision": global_precision, "Recall": global_recall, "F1 Score": global_f1}}
